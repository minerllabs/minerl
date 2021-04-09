package com.microsoft.Malmo.Mixins;

import net.minecraft.block.state.IBlockState;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.item.ItemBucket;
import net.minecraft.item.ItemStack;
import net.minecraft.nbt.NBTTagCompound;
import net.minecraft.stats.StatList;
import net.minecraft.util.EnumActionResult;
import net.minecraft.util.EnumFacing;
import net.minecraft.util.EnumHand;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;
import net.minecraft.world.chunk.Chunk;
import net.minecraftforge.common.ForgeHooks;
import net.minecraftforge.common.util.BlockSnapshot;
import net.minecraftforge.event.ForgeEventFactory;
import net.minecraftforge.event.world.BlockEvent;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Overwrite;

import javax.annotation.Nonnull;
import java.util.Iterator;
import java.util.List;

@Mixin(ForgeHooks.class)
public abstract class MixinForgeHookStatsFix {
    /**
     * @author Joost Huizinga
     */
    @Overwrite
    public static EnumActionResult onPlaceItemIntoWorld(@Nonnull ItemStack itemstack, @Nonnull EntityPlayer player, @Nonnull World world, @Nonnull BlockPos pos, @Nonnull EnumFacing side, float hitX, float hitY, float hitZ, @Nonnull EnumHand hand) {
        int meta = itemstack.getItemDamage();
        int size = itemstack.getCount();
        NBTTagCompound nbt = null;
        if (itemstack.getTagCompound() != null) {
            nbt = itemstack.getTagCompound().copy();
        }

        if (!(itemstack.getItem() instanceof ItemBucket)) {
            world.captureBlockSnapshots = true;
        }

        EnumActionResult ret = itemstack.getItem().onItemUse(player, world, pos, hand, side, hitX, hitY, hitZ);
        world.captureBlockSnapshots = false;
        if (ret == EnumActionResult.SUCCESS) {
            int newMeta = itemstack.getItemDamage();
            int newSize = itemstack.getCount();
            NBTTagCompound newNBT = null;
            if (itemstack.getTagCompound() != null) {
                newNBT = itemstack.getTagCompound().copy();
            }

            BlockEvent.PlaceEvent placeEvent = null;
            List<BlockSnapshot> blockSnapshots = (List)world.capturedBlockSnapshots.clone();
            world.capturedBlockSnapshots.clear();
            itemstack.setItemDamage(meta);
            itemstack.setCount(size);
            if (nbt != null) {
                itemstack.setTagCompound(nbt);
            }

            if (blockSnapshots.size() > 1) {
                placeEvent = ForgeEventFactory.onPlayerMultiBlockPlace(player, blockSnapshots, side, hand);
            } else if (blockSnapshots.size() == 1) {
                placeEvent = ForgeEventFactory.onPlayerBlockPlace(player, (BlockSnapshot)blockSnapshots.get(0), side, hand);
            }

            Iterator var18;
            BlockSnapshot snap;
            if (placeEvent != null && ((BlockEvent.PlaceEvent)placeEvent).isCanceled()) {
                ret = EnumActionResult.FAIL;

                for(var18 = blockSnapshots.iterator(); var18.hasNext(); world.restoringBlockSnapshots = false) {
                    snap = (BlockSnapshot)var18.next();
                    world.restoringBlockSnapshots = true;
                    snap.restore(true, false);
                }
            } else {
                itemstack.setItemDamage(newMeta);
                itemstack.setCount(newSize);

                if (nbt != null) {
                    itemstack.setTagCompound(newNBT);
                }

                int updateFlag;
                IBlockState oldBlock;
                IBlockState newBlock;
                for(var18 = blockSnapshots.iterator(); var18.hasNext(); world.markAndNotifyBlock(snap.getPos(), (Chunk)null, oldBlock, newBlock, updateFlag)) {
                    snap = (BlockSnapshot)var18.next();
                    updateFlag = snap.getFlag();
                    oldBlock = snap.getReplacedBlock();
                    newBlock = world.getBlockState(snap.getPos());
                    if (!newBlock.getBlock().hasTileEntity(newBlock)) {
                        newBlock.getBlock().onBlockAdded(world, snap.getPos(), newBlock);
                    }
                }

                // BUGFIX: Get the actual item of the stack, regardless of whether the stack is empty
                if (itemstack.getCount() == 0) itemstack.setCount(1);
                player.addStat(StatList.getObjectUseStats(itemstack.getItem()));
                itemstack.setCount(newSize);
                // BUGFIX: end
                // Original code:
                // player.addStat(StatList.getObjectUseStats(itemstack.getItem()));
            }
        }

        world.capturedBlockSnapshots.clear();
        return ret;
    }

}
