package com.microsoft.Malmo.Mixins;
import com.google.common.collect.Lists;
import net.minecraft.block.Block;
import net.minecraft.item.Item;
import net.minecraft.init.Items;
import net.minecraft.stats.AchievementList;
import net.minecraft.stats.StatBase;
import net.minecraft.stats.StatCrafting;
import net.minecraft.stats.StatList;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Overwrite;
import org.spongepowered.asm.mixin.Shadow;
import org.apache.logging.log4j.LogManager;
import com.microsoft.Malmo.Utils.CraftingHelper;
import java.util.List;



@Mixin(StatList.class)
public abstract class MixinMergeStatsFix {
    @Final
    @Shadow public static final List<StatBase> ALL_STATS = Lists.<StatBase>newArrayList();
    @Final
    @Shadow public static final List<StatBase> BASIC_STATS = Lists.<StatBase>newArrayList();
    @Final
    @Shadow public static final List<StatCrafting> MINE_BLOCK_STATS = Lists.<StatCrafting>newArrayList();
    @Shadow private static void initMiningStats(){}
    @Shadow private static void initItemDepleteStats(){}
    @Shadow private static void initStats(){}
    @Shadow private static void initCraftableStats(){}
    @Shadow private static void initPickedUpAndDroppedStats(){}

    // An alternate option would be to not do any merging. However, I think there is a potential for null-pointer
    // exceptions if we do so.
//    /**
//     * @author Joost Huizinga
//     */
//    @Overwrite
//    private static void replaceAllSimilarBlocks(StatBase[] stat, boolean useItemIds)
//    {
//        // Don't replace anything
//    }

    /**
     * @author Joost Huizinga
     */
    @Overwrite
    private static void mergeStatBases(StatBase[] statBaseIn, Block block1, Block block2, boolean useItemIds)
    {
        int i;
        int j;
        if (useItemIds) {
            i = Item.getIdFromItem(Item.getItemFromBlock(block1));
            j = Item.getIdFromItem(Item.getItemFromBlock(block2));
            if (i == Item.getIdFromItem(Items.AIR) || j == Item.getIdFromItem(Items.AIR) || i == j) {
                // If any of these conditions is true, the merge won't actually do anything, or it will remove
                // valid statistics.
                return;
            }
        } else {
            i = Block.getIdFromBlock(block1);
            j = Block.getIdFromBlock(block2);
        }
        if (statBaseIn[i] != null && statBaseIn[j] == null)
        {
            statBaseIn[j] = statBaseIn[i];
        }
        else if(statBaseIn[i] == null && statBaseIn[j] != null) {
            statBaseIn[j] = statBaseIn[i];
        }
        // The below code would actually merge the stats if both exist.
        // We chose not to do this merge, but to keep them separate instead.
//        else if(statBaseIn[i] != null && statBaseIn[j] != null)
//        {
//            if (statBaseIn[i] != statBaseIn[j]) {
//                ALL_STATS.remove(statBaseIn[i]);
//                MINE_BLOCK_STATS.remove(statBaseIn[i]);
//                BASIC_STATS.remove(statBaseIn[i]);
//                statBaseIn[i] = statBaseIn[j];
//            }
//        }
    }

    /**
     * @author Joost Huizinga
     */
    @Overwrite
    public static void init()
    {
        LogManager.getLogger().warn("============= Init mining stats (BLOCKS_STATS) =============");
        initMiningStats();
//        for (StatBase stat : StatList.ALL_STATS) {
//            if (stat.statId.contains("furnace")) {
//                LogManager.getLogger().warn("Stat: " + stat.statId);
//            }
//        }
        LogManager.getLogger().warn("============= Init stats (OBJECT_USE_STATS) =============");
        initStats();
//        for (StatBase stat : StatList.ALL_STATS) {
//            if (stat.statId.contains("furnace")) {
//                LogManager.getLogger().warn("Stat: " + stat.statId);
//            }
//        }
        LogManager.getLogger().warn("============= initItemDepleteStats (OBJECT_BREAK_STATS) =============");
        initItemDepleteStats();
//        for (StatBase stat : StatList.ALL_STATS) {
//            if (stat.statId.contains("furnace")) {
//                LogManager.getLogger().warn("Stat: " + stat.statId);
//            }
//        }
        LogManager.getLogger().warn("============= initCraftableStats (CRAFTS_STATS) =============");
        initCraftableStats();
//        for (StatBase stat : StatList.ALL_STATS) {
//            if (stat.statId.contains("furnace")) {
//                LogManager.getLogger().warn("Stat: " + stat.statId);
//            }
//        }
        LogManager.getLogger().warn("============= initPickedUpAndDroppedStats (OBJECT_BREAK_STATS) =============");
        initPickedUpAndDroppedStats();
//        for (StatBase stat : StatList.ALL_STATS) {
//            if (stat.statId.contains("furnace")) {
//                LogManager.getLogger().warn("Stat: " + stat.statId);
//            }
//        }
        LogManager.getLogger().warn("============= AchievementList.init() =============");
        AchievementList.init();
        CraftingHelper.dumpMinecraftObjectRules("/Users/joost/openai/minerl/minerl/herobraine/hero/mc_constants.json");

//        for (StatBase stat : StatList.ALL_STATS) {
//            if (stat.statId.contains("furnace")) {
//                LogManager.getLogger().warn("Stat: " + stat.statId);
//            }
//        }
    }
}
