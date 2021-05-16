// --------------------------------------------------------------------------------------------------
//  Copyright (c) 2016 Microsoft Corporation
//  
//  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
//  associated documentation files (the "Software"), to deal in the Software without restriction,
//  including without limitation the rights to use, copy, modify, merge, publish, distribute,
//  sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
//  furnished to do so, subject to the following conditions:
//  
//  The above copyright notice and this permission notice shall be included in all copies or
//  substantial portions of the Software.
//  
//  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
//  NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
//  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
//  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
// --------------------------------------------------------------------------------------------------

package com.microsoft.Malmo.MissionHandlers;

import com.google.common.base.CharMatcher;
import com.microsoft.Malmo.Utils.MineRLTypeHelper;
import io.netty.buffer.ByteBuf;

import com.microsoft.Malmo.MalmoMod;
import com.microsoft.Malmo.MissionHandlerInterfaces.ICommandHandler;
import com.microsoft.Malmo.Schemas.*;
import com.microsoft.Malmo.Schemas.MissionInit;
import net.minecraft.block.Block;
import net.minecraft.client.Minecraft;
import net.minecraft.entity.player.EntityPlayerMP;
import net.minecraft.entity.player.InventoryPlayer;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.util.ResourceLocation;
import net.minecraft.util.math.AxisAlignedBB;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.RayTraceResult;

import net.minecraftforge.fml.common.network.ByteBufUtils;
import net.minecraftforge.fml.common.network.simpleimpl.IMessage;
import net.minecraftforge.fml.common.network.simpleimpl.IMessageHandler;
import net.minecraftforge.fml.common.network.simpleimpl.MessageContext;

import javax.annotation.Resource;

/**
 * @author Brandon Houghton, Carnegie Mellon University
 * <p>
 * Equip commands allow agents to equip any item in their inventory worry about slots or hotbar location.
 */
public class EquipCommandsImplementation extends CommandBase {
    private boolean isOverriding;

    public static class EquipMessage implements IMessage {
        private String parameters;
        private String itemType;
        private Integer metadata;

        public EquipMessage(){}

        public EquipMessage(String parameters) {
            setParameters(parameters);
        }

        private void setParameters(String parameters) {
            this.parameters = parameters;
            String[] parts = parameters.split("#");
            if (parts.length != 2) {
                throw new IllegalArgumentException(String.format("Bad parameter: '%s'", parameters));
            }
            itemType = parts[0];
            assert parts[0].length() > 0;

            // TODO(shwang): Support null value for metadata via something like `parameters = "metadata#~"`.
            metadata = Integer.parseInt(parts[1]);
            assert metadata >= 0 && metadata < 16;
        }

        public String getItemType() {
            return itemType;
        }

        public int getMetadata() {
            return metadata;
        }

        public boolean validateItemType() {
            // Sometimes we intentionally send invalid itemType from MineRL -- e.g. "other". In these cases we
            // should just drop the packet. Ideally, we would error on all unexpected cases... (excluding
            // "other" and "none"). For now, there seems to be the default behavior of explicitly ignoring "none".
            Item item = Item.getByNameOrId(getItemType());
            return item != null && item.getRegistryName() != null && !getItemType().equalsIgnoreCase("none");
        }

        @Override
        public void fromBytes(ByteBuf buf) {
            setParameters(ByteBufUtils.readUTF8String(buf));
        }

        @Override
        public void toBytes(ByteBuf buf) {
            ByteBufUtils.writeUTF8String(buf, this.parameters);
        }
    }

    public static class EquipMessageHandler implements IMessageHandler<EquipMessage, IMessage> {
        @Override
        public IMessage onMessage(EquipMessage message, MessageContext ctx) {
            EntityPlayerMP player = ctx.getServerHandler().playerEntity;
            if (player == null)
                return null;

            InventoryPlayer inv = player.inventory;
            Integer matchIdx = MineRLTypeHelper.inventoryIndexOf(inv, message.getItemType(), message.getMetadata());

            if (matchIdx != null) {
                // Swap current hotbar item with found inventory item (if not the same)
                int hotbarIdx = player.inventory.currentItem;
                System.out.println("got hotbar idx" + hotbarIdx);
                System.out.println("got slot " + matchIdx);

                ItemStack prevEquip = inv.getStackInSlot(hotbarIdx).copy();
                ItemStack matchingStack = inv.getStackInSlot(matchIdx).copy();
                inv.setInventorySlotContents(hotbarIdx, matchingStack);
                inv.setInventorySlotContents(matchIdx, prevEquip);
            }

            return null;
        }
    }

    @Override
    protected boolean onExecute(String verb, String parameter, MissionInit missionInit) {
        if (!verb.equalsIgnoreCase("equip"))
            return false;

        EquipMessage msg = new EquipMessage(parameter);
        if (msg.validateItemType()) {
            MalmoMod.network.sendToServer(msg);
        }
        return true;  // Packet is captured by equip handler
    }

    @Override
    public boolean parseParameters(Object params) {
        if (!(params instanceof EquipCommands))
            return false;

            EquipCommands pParams = (EquipCommands) params;
        // Todo: Implement allow and deny lists.
        // setUpAllowAndDenyLists(pParams.getModifierList());
        return true;
    }

    @Override
    public void install(MissionInit missionInit) {
    }

    @Override
    public void deinstall(MissionInit missionInit) {
    }

    @Override
    public boolean isOverriding() {
        return this.isOverriding;
    }

    @Override
    public void setOverriding(boolean b) {
        this.isOverriding = b;
    }
}
