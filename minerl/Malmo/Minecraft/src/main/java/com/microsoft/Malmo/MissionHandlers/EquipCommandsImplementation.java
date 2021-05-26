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

import com.microsoft.Malmo.Utils.MineRLTypeHelper;

import com.microsoft.Malmo.MalmoMod;
import com.microsoft.Malmo.Schemas.*;
import com.microsoft.Malmo.Schemas.MissionInit;
import net.minecraft.entity.player.EntityPlayerMP;
import net.minecraft.entity.player.InventoryPlayer;
import net.minecraft.item.ItemStack;

import net.minecraftforge.fml.common.network.simpleimpl.IMessage;
import net.minecraftforge.fml.common.network.simpleimpl.IMessageHandler;
import net.minecraftforge.fml.common.network.simpleimpl.MessageContext;

/**
 * @author Brandon Houghton, Carnegie Mellon University
 * <p>
 * Equip commands allow agents to equip any item in their inventory worry about slots or hotbar location.
 */
public class EquipCommandsImplementation extends CommandBase {
    private boolean isOverriding;

    public static class EquipMessageHandler
            implements IMessageHandler<MineRLTypeHelper.ItemTypeMetadataMessage, IMessage> {
        @Override
        public IMessage onMessage(MineRLTypeHelper.ItemTypeMetadataMessage message, MessageContext ctx) {
            EntityPlayerMP player = ctx.getServerHandler().playerEntity;
            if (player == null)
                return null;

            InventoryPlayer inv = player.inventory;
            System.out.printf("Equip: Should be switching to <item_type=%s, metadata=%s>%n",
                    message.getItemType(), message.getMetadata()
                    );
            Integer matchIdx = MineRLTypeHelper.inventoryIndexOf(inv, message.getItemType(), message.getMetadata());
            System.out.printf("Equip: Found match index: %s%n", matchIdx);

            if (matchIdx != null) {
                // Swap current hotbar item with found inventory item (if not the same)
                int hotbarIdx = inv.currentItem;
                System.out.println("got hotbar idx" + hotbarIdx);
                System.out.println("got slot " + matchIdx);

                ItemStack prevEquip = inv.getStackInSlot(hotbarIdx).copy();
                ItemStack matchingStack = inv.getStackInSlot(matchIdx).copy();
                ObservationFromEquippedItemImplementation.printEquipmentJSON();
                System.out.printf("Equip: prevEquip=%s, to be swapped with newEquip=%s%n", prevEquip, matchingStack);
                inv.setInventorySlotContents(hotbarIdx, matchingStack);
                inv.setInventorySlotContents(matchIdx, prevEquip);

                System.out.printf("Equip: Now, hotbar_idx=%s is holding: %s%n",
                        hotbarIdx, inv.getStackInSlot(hotbarIdx));
                ObservationFromEquippedItemImplementation.printEquipmentJSON();
                System.out.printf("Equip: (double-check) Now, hotbar_idx=%s is holding: %s%n",
                        hotbarIdx, player.inventory.getStackInSlot(hotbarIdx));
            }

            return null;
        }
    }

    @Override
    protected boolean onExecute(String verb, String parameter, MissionInit missionInit) {
        System.out.printf("equip: enter onExecute verb=%s parameter=%s%n", verb, parameter);
        System.out.println("basalt ballast #1");
        System.out.println("basalt ballast #2");
        System.out.println("basalt ballast #3");
        if (!verb.equalsIgnoreCase("equip")) {
            System.out.printf("equip: rejecting verb=%s%n", verb);
            return false;
        }
        System.out.printf("equip: accepting verb=%s%n", verb);

        MineRLTypeHelper.ItemTypeMetadataMessage msg = new MineRLTypeHelper.ItemTypeMetadataMessage(parameter);
        System.out.printf("equip: validateItemType %s%n", msg.validateItemType());
        if (msg.validateItemType()) {
            MalmoMod.network.sendToServer(msg);
        } else {
            System.out.printf("equip: rejecting due to validateItemType %s%n", msg.validateItemType());
        }
        return true;  // Packet is captured by equip handler
    }

    @Override
    public boolean parseParameters(Object params) {
        System.out.printf("equip: enter parse parameters to process %s%n", params);
        if (!(params instanceof EquipCommands))
            return false;
        System.out.printf("equip: parse parameters ACCEPTS %s%n", params);

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
