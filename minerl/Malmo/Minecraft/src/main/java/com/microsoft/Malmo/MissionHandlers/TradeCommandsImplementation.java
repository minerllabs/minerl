package com.microsoft.Malmo.MissionHandlers;

import com.microsoft.Malmo.MalmoMod;
import com.microsoft.Malmo.Schemas.TradeCommand;
import com.microsoft.Malmo.Schemas.TradeCommands;
import com.microsoft.Malmo.Schemas.MissionInit;
import com.microsoft.Malmo.Utils.TimeHelper;
import io.netty.buffer.ByteBuf;
import net.minecraft.client.Minecraft;
import net.minecraft.entity.Entity;
import net.minecraft.entity.player.EntityPlayerMP;
import net.minecraft.inventory.IInventory;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.server.management.PlayerList;
import net.minecraft.tileentity.TileEntity;
import net.minecraft.tileentity.TileEntityEnderChest;
import net.minecraft.tileentity.TileEntityLockableLoot;
import net.minecraft.util.IThreadListener;
import net.minecraft.util.ResourceLocation;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.RayTraceResult;
import net.minecraft.world.WorldServer;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.common.FMLCommonHandler;
import net.minecraftforge.fml.common.network.ByteBufUtils;
import net.minecraftforge.fml.common.network.simpleimpl.IMessage;
import net.minecraftforge.fml.common.network.simpleimpl.IMessageHandler;
import net.minecraftforge.fml.common.network.simpleimpl.MessageContext;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** A simple trading command.
 */
public class TradeCommandsImplementation extends CommandGroup
{
    public static class TradeMessage implements IMessage
    {
        String target;
        Map<String, Integer> trades;

        public TradeMessage()
        {
        }

        public TradeMessage(String target, Map<String, Integer> trades)
        {
            this.target = target;
            this.trades = trades;
        }

        @Override
        public void fromBytes(ByteBuf buf)
        {
            this.target = ByteBufUtils.readUTF8String(buf);
            this.trades = new HashMap<String, Integer>();
            int toRead = buf.readInt();
            for (int i = 0; i < toRead; i++) {
                String key = ByteBufUtils.readUTF8String(buf);
                int val = buf.readInt();
                this.trades.put(key, val);
            }
        }

        @Override
        public void toBytes(ByteBuf buf)
        {
            ByteBufUtils.writeUTF8String(buf, this.target);
            buf.writeInt(this.trades.size());
            int n_written = 0;
            for (Map.Entry<String, Integer> entry: this.trades.entrySet()) {
                ByteBufUtils.writeUTF8String(buf, entry.getKey());
                buf.writeInt(entry.getValue());
                n_written += 1;
            }
        }
    }

    public static class TradeMessageHandler implements IMessageHandler<TradeMessage, IMessage>
    {
        @Override
        public IMessage onMessage(final TradeMessage message, MessageContext ctx)
        {
            final EntityPlayerMP source = ctx.getServerHandler().playerEntity;
            IThreadListener mainThread = (WorldServer)ctx.getServerHandler().playerEntity.world;
            // TODO: does this really need to run on the main thread or??? yesss
            mainThread.addScheduledTask(new Runnable() {
                @Override
                public void run() {
                    PlayerList playerList = FMLCommonHandler.instance().getMinecraftServerInstance().getPlayerList();
                    EntityPlayerMP target = playerList.getPlayerByUsername(message.target);
                    if (source == null || target == null) {
                        return;
                    }

                    // Check that the trade can actually be completed.
                    Map<String, Integer> sourceInv = new HashMap<String, Integer>();
                    int sourceFreeSlots = playerInventoryToMap(source, sourceInv);
                    Map<String, Integer> targetInv = new HashMap<String, Integer>();
                    int targetFreeSlots = playerInventoryToMap(target, targetInv);
                    for (Map.Entry<String, Integer> entry : message.trades.entrySet()) {
                        Item item = Item.getByNameOrId(entry.getKey());
                        if (item == null) {
                            // Invalid item
                            throw new RuntimeException("Unknown item in trading " + entry.getKey());
                        }
                        String name = item.getRegistryName().toString();
                        if (entry.getValue() < 0) {
                            // Negative means the SOURCE will lose the item, and the target will gain it

                            // We check that sourceInv has enough of the item
                            if (sourceInv.getOrDefault(name, 0) < -entry.getValue()) {
                                return;
                            }
                            // We subtract 1 from the number of free slots in the target
                            // TODO: in some cases this might not be necessary because we can reuse an existing stack,
                            //  but this is the easiest way to do it.
                            targetFreeSlots--;
                        } else {
                            // We do the opposite as above
                            if (targetInv.getOrDefault(name, 0) < entry.getValue()) {
                                return;
                            }
                            sourceFreeSlots--;
                        }
                    }
                    if (sourceFreeSlots < 0 || targetFreeSlots < 0) {
                        // Not enough free slots in the inventory.
                        return;
                    }

                    // Complete the trade
                    for (Map.Entry<String, Integer> entry : message.trades.entrySet()) {
                        if (entry.getValue() < 0) {
                            give(source, target, entry.getKey(), -entry.getValue());
                            TimeHelper.SyncManager.debugLog("Gave " + (new Integer(-entry.getValue())).toString() + " " + entry.getKey() + " from " + source.getName() + " to " + target.getName());
                        }
                        else {
                            give(target, source, entry.getKey(), entry.getValue());
                            TimeHelper.SyncManager.debugLog("Gave " + (new Integer(entry.getValue())).toString() + " " + entry.getKey() + " from " + target.getName() + " to " + source.getName());
                        }
                    }
                }

                private void give(EntityPlayerMP source, EntityPlayerMP target, String name, int quantity) {
                    ResourceLocation item = Item.getByNameOrId(name).getRegistryName();
                    ItemStack sourceStackExample = null;
                    int sourceItemsToFind = quantity;
                    for (int i = 0; sourceItemsToFind > 0 && i < source.inventory.getSizeInventory(); i++) {
                        ItemStack stack = source.inventory.getStackInSlot(i);
                        if (stack.getItem().getRegistryName() != null && stack.getItem().getRegistryName().equals(item)) {
                            if (sourceStackExample == null) {
                                sourceStackExample = stack.copy();
                            }
                            if (stack.getCount() <= sourceItemsToFind) {
                                sourceItemsToFind -= stack.getCount();
                                source.inventory.removeStackFromSlot(i);
                            }
                            else {
                                stack.setCount(stack.getCount() - sourceItemsToFind);
                                sourceItemsToFind = 0;
                            }
                        }
                    }
                    if (sourceStackExample == null) {
                        // This should never happen, but we fail silently.
                        throw new RuntimeException("Could not find source stack for trading " + name + " even after double checking. This should not happen.");
                    }

                    int targetItemsToGive = quantity;
                    while (targetItemsToGive > 0) {
                        ItemStack giveStack = sourceStackExample.copy();
                        if (targetItemsToGive <= giveStack.getMaxStackSize()) {
                            giveStack.setCount(targetItemsToGive);
                        } else {
                            giveStack.setCount(giveStack.getMaxStackSize());
                        }
                        targetItemsToGive -= giveStack.getCount();
                        if (!target.inventory.addItemStackToInventory(giveStack)) {
                            throw new RuntimeException("Giving target item " + name + " failed during trading. This should never happen but continuing anyway: it's too late to turn back now.");
                        }
                    }
                }

                private int playerInventoryToMap(EntityPlayerMP player, Map<String, Integer> inventory) {
                    int freeSlots = 0;
                    Map<String, Integer> sourceInv = new HashMap<String, Integer>();
                    for (int i = 0; i < player.inventory.getSizeInventory(); i++) {
                        ItemStack stack = player.inventory.getStackInSlot(i);
                        ResourceLocation itemName = stack.getItem().getRegistryName();
                        if (itemName == null || stack.isEmpty()) {
                            freeSlots++;
                        } else {
                            TimeHelper.SyncManager.debugLog("Slot " + itemName.toString() + " " + String.valueOf(stack.getCount()));
                            inventory.put(itemName.toString(), inventory.getOrDefault(itemName.toString(), 0) + stack.getCount());
                        }
                    }
                    TimeHelper.SyncManager.debugLog("Free slots: " + String.valueOf(freeSlots));
                    return freeSlots;
                }
            });
            return null;
        }
    }

    TradeCommandsImplementation() {
        super();
    }

    @Override
    public boolean parseParameters(Object params)
    {
        super.parseParameters(params);

        if (params == null || !(params instanceof TradeCommands))
            return false;

        TradeCommands iparams = (TradeCommands) params;
        setUpAllowAndDenyLists(iparams.getModifierList());
        return true;
    }

    @Override
    protected boolean onExecute(String verb, String parameter, MissionInit missionInit)
    {
        if (verb.equalsIgnoreCase(TradeCommand.TRADE.value()))
        {
            if (parameter != null && parameter.length() != 0)
            {
                String[] params = parameter.split(" ");
                if (params.length < 2) {
                    TimeHelper.SyncManager.debugLog("Fewer than 2 tokens: " + parameter);
                    // We need at least a target and one item to send
                    return false;
                }
                String target = params[0];
                Map<String, Integer> trades = new HashMap<String, Integer>();
                for (int i = 1; i < params.length; i++) {
                    String[] itemDesc = params[i].split(":");
                    if (itemDesc.length != 2) {
                        TimeHelper.SyncManager.debugLog("Does not contain 2 sides: " + params[i]);
                        // There should be an item name and a number
                        return false;
                    }
                    try {
                        int toAdd = Integer.parseInt(itemDesc[1]);
                        trades.put(itemDesc[0], trades.getOrDefault(itemDesc[0], 0) + toAdd);
                    } catch (NumberFormatException e) {
                        TimeHelper.SyncManager.debugLog("Not a number: " + itemDesc[1]);
                        // Not a proper number as the item number
                        return false;
                    }
                }

                // All okay, so create a trade message for the server:
                MalmoMod.network.sendToServer(new TradeMessage(target, trades));
                return true;
            }
        }
        return super.onExecute(verb, parameter, missionInit);
    }

    @Override
    public boolean isFixed() { return true; }
}