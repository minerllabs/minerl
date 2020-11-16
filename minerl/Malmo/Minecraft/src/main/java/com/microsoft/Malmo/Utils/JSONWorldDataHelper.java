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

package com.microsoft.Malmo.Utils;

import com.google.common.base.CaseFormat;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;

import net.minecraft.block.Block;
import net.minecraft.block.state.IBlockState;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.entity.player.EntityPlayerMP;
import net.minecraft.item.Item;
import net.minecraft.stats.*;
import net.minecraft.util.Tuple;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.ResourceLocation;

import net.minecraft.stats.StatList;
import net.minecraft.stats.StatisticsManagerServer;
import net.minecraft.world.biome.Biome;

import javax.lang.model.element.Element;
import javax.lang.model.element.UnknownElementException;
import javax.swing.*;
import java.util.*;
import java.util.function.Function;

import static net.minecraft.stats.StatList.*;

/**
 * Helper class for building the "World data" to be passed from Minecraft back to the agent.<br>
 * This class contains helper methods to build up a JSON tree of useful information, such as health, XP, food levels, distance travelled, etc.etc.<br>
 * It can also build up a grid of the block types around the player or somewhere else in the world.
 * Call this on the Server side only.
 */
public class JSONWorldDataHelper
{
    /**
     * Simple class to hold the dimensions of the environment
     * that we want to return in the World Data.<br>
     * Min and max define an inclusive range, where the player's feet are situated at (0,0,0) if absoluteCoords=false.
     */
    static public class GridDimensions {
        public int xMin;
        public int xMax;
        public int yMin;
        public int yMax;
        public int zMin;
        public int zMax;
        public boolean absoluteCoords;
        public boolean projectDown;

        /**
         * Default constructor asks for an environment just big enough to contain
         * the player and one block all around him.
         */
        public GridDimensions() {
            this.xMin = -1; this.xMax = 1;
            this.zMin = -1; this.zMax = 1;
            this.yMin = -1; this.yMax = 2;
            this.absoluteCoords = false;
            this.projectDown = false;
        }

        /**
         * Convenient constructor - effectively specifies the margin around the player<br>
         * Passing (1,1,1) will have the same effect as the default constructor.
         * @param xMargin number of blocks to the left and right of the player
         * @param yMargin number of blocks above and below player
         * @param zMargin number of blocks in front of and behind player
         */
        public GridDimensions(int xMargin, int yMargin, int zMargin) {
            this.xMin = -xMargin; this.xMax = xMargin;
            this.yMin = -yMargin; this.yMax = yMargin + 1;  // +1 because the player is two blocks tall.
            this.zMin = -zMargin; this.zMax = zMargin;
            this.absoluteCoords = false;
            this.projectDown = false;
        }

        /**
         * Convenient constructor for the case where all that is required is the flat patch of ground<br>
         * around the player's feet.
         * @param xMargin number of blocks around the player in the x-axis
         * @param zMargin number of blocks around the player in the z-axis
         */
        public GridDimensions(int xMargin, int zMargin) {
            this.xMin = -xMargin; this.xMax = xMargin;
            this.yMin = -1; this.yMax = -1;  // Flat patch of ground at the player's feet.
            this.zMin = -zMargin; this.zMax = zMargin;
            this.absoluteCoords = false;
            this.projectDown = false;
        }
    };

    /** Builds the basic achievement world data to be used as observation signals by the listener.
     * @param json a JSON object into which the achievement stats will be added.
     */
    public static void buildBaseMinecraftStats(JsonObject json, EntityPlayerSP player)
    {
        StatisticsManager statisticsManager = player.getStatFileWriter();

        json.addProperty("distance_travelled_cm",
            statisticsManager.readStat(StatList.WALK_ONE_CM)
            + statisticsManager.readStat(StatList.CROUCH_ONE_CM)
            + statisticsManager.readStat(StatList.SPRINT_ONE_CM)
            + statisticsManager.readStat(StatList.SWIM_ONE_CM)
            + statisticsManager.readStat(StatList.FALL_ONE_CM)
            + statisticsManager.readStat(StatList.CLIMB_ONE_CM)
            + statisticsManager.readStat(StatList.FLY_ONE_CM)
            + statisticsManager.readStat(StatList.DIVE_ONE_CM)
            + statisticsManager.readStat(StatList.MINECART_ONE_CM)
            + statisticsManager.readStat(StatList.BOAT_ONE_CM)
            + statisticsManager.readStat(StatList.PIG_ONE_CM)
            + statisticsManager.readStat(StatList.HORSE_ONE_CM)
            + statisticsManager.readStat(StatList.AVIATE_ONE_CM)
            );

        for(StatBase stat : StatList.ALL_STATS) {
            // For MineRL, split over . and convert all camelCase to snake_case
            String[] stat_fields = stat.statId.split("\\.");
            JsonObject head = json;
            for (String unformatted_token : stat_fields) {
                String token = CaseFormat.UPPER_CAMEL.to(CaseFormat.LOWER_UNDERSCORE, unformatted_token);
                // Last element is a leaf
                if (unformatted_token.equals(stat_fields[stat_fields.length - 1])) {
                    // BAH map drop stat to items_dropped to prevent hash collision in dict keys
                    // MUST change this in CraftingHelper.java as well!!!! (search above comment)
                    if (token.equals("drop"))
                        token = "items_dropped";
                    head.addProperty(token, statisticsManager.readStat(stat));
                } else {
                    if (head.has(token))
                        if (head.get(token) instanceof JsonObject)
                            head = head.getAsJsonObject(token);
                        else {
                            System.out.println("Duplicate token! " + Arrays.toString(stat_fields));
                            head.remove(token);
                            JsonObject newRoot = new JsonObject();
                            head.add(token, newRoot);
                            head = newRoot;
                        }
                    else {
                        JsonObject newRoot = new JsonObject();
                        head.add(token, newRoot);
                        head = newRoot;
                    }
                }
            }
        }
    }

    /** Builds the basic life world data to be used as observation signals by the listener.
     * @param json a JSON object into which the life stats will be added.
     */
    public static void buildLifeStats(JsonObject json, EntityPlayerSP player)
    {
        json.addProperty("life", player.getHealth());
        json.addProperty("score", player.getScore());    // Might always be the same as XP?
        json.addProperty("food", player.getFoodStats().getFoodLevel());
        json.addProperty("saturation", player.getFoodStats().getSaturationLevel());
        json.addProperty("xp", player.experienceTotal);
        json.addProperty("is_alive", !player.isDead);
        json.addProperty("air", player.getAir());
        json.addProperty("name", player.getName());
    }
    /** Builds the player position data to be used as observation signals by the listener.
     * @param json a JSON object into which the positional information will be added.
     */
    public static void buildPositionStats(JsonObject json, EntityPlayerSP player)
    {
        json.addProperty("xpos",  player.posX);
        json.addProperty("ypos",  player.posY);
        json.addProperty("zpos", player.posZ);
        json.addProperty("pitch",  player.rotationPitch);
        json.addProperty("yaw", player.rotationYaw);
    }

    /** Builds the player's biome data.
     * @param json a JSON object into which the biome information will be added.
     * @param player - Non-null, must have player.world
     */
    public static void buildBiomeStats(JsonObject json, EntityPlayerSP player)
    {
        BlockPos playerPos = player.getPosition();
        Biome playerBiome = player.world.getBiome(playerPos);
        // Name of the current biome
        json.addProperty("biome_name", playerBiome.getBiomeName());
        // ID of the current biome
        json.addProperty("biome_id", Biome.getIdForBiome(playerBiome));
        // The average temperature of the current biome
        json.addProperty("biome_temperature", playerBiome.getTemperature());
        // The average rainfall chance of the current biome
        json.addProperty("biome_rainfall", playerBiome.getRainfall());
        // The water level for oceans and rivers
        json.addProperty("sea_level", player.world.getSeaLevel());
    }

    /** Builds the player's weather information
     * @param json a JSON object into which the weather information will be added.
     * @param player - Non-null, must have player.world
     */
    public static void buildWeatherStats(JsonObject json, EntityPlayerSP player)
    {
        BlockPos playerPos = player.getPosition();
        json.addProperty("light_level", player.world.getLight(playerPos));
        // If it is currently precipitating here
        json.addProperty("is_raining", player.world.isRaining());
        // If the playerPos has LOS to the sky
        json.addProperty("can_see_sky", player.world.canSeeSky(playerPos));
        // [0, 1] Brightness factor of the sun
        json.addProperty("sun_brightness", player.world.getSunBrightnessFactor(0));
        // [0, 1] Light level provided by the sky
        json.addProperty("sky_light_level", player.world.getSunBrightness(0));
        // TODO add other statuses such as is_raining or other current weather
    }

    public static void buildEnvironmentStats(JsonObject json, EntityPlayerSP player)
    {
        json.addProperty("world_time", player.world.getWorldTime());  // Current time in ticks
        json.addProperty("total_time", player.world.getTotalWorldTime());  // Total time world has been running
    }
    /**
     * Build a signal for the cubic block grid centred on the player.<br>
     * Default is 3x3x4. (One cube all around the player.)<br>
     * Blocks are returned as a 1D array, in order
     * along the x, then z, then y axes.<br>
     * Data will be returned in an array called "Cells"
     * @param json a JSON object into which the info for the object under the mouse will be added.
     * @param environmentDimensions object which specifies the required dimensions of the grid to be returned.
     * @param jsonName name to use for identifying the returned JSON array.
     */
    public static void buildGridData(JsonObject json, GridDimensions environmentDimensions, EntityPlayerMP player, String jsonName)
    {
        if (player == null || json == null)
            return;

        JsonArray arr = new JsonArray();
        BlockPos pos = new BlockPos(player.posX, player.posY, player.posZ);
        // TODO peterz implement projection in any direction, not only down in y
        // direction
        if (environmentDimensions.projectDown)
        {
            for (int z = environmentDimensions.zMin; z <= environmentDimensions.zMax; z++)
            {
                for (int x = environmentDimensions.xMin; x <= environmentDimensions.xMax; x++)
                {
                    for (int y = environmentDimensions.yMax; y >= environmentDimensions.yMin; y--) {
                        BlockPos p;
                        if (environmentDimensions.absoluteCoords)
                            p = new BlockPos(x, y, z);
                        else
                            p = pos.add(x, y, z);
                        String name = "";
                        IBlockState state = player.world.getBlockState(p);
                        Object blockName = Block.REGISTRY.getNameForObject(state.getBlock());
                        if (blockName instanceof ResourceLocation) {
                            name = ((ResourceLocation) blockName).getResourcePath();
                        }
                        if (name.equals("air"))
                            continue;
                        JsonElement element = new JsonPrimitive(name);
                        arr.add(element);
                        break;
                    }
                }
            }
        } else {
            for (int y = environmentDimensions.yMin; y <= environmentDimensions.yMax; y++) {
                for (int z = environmentDimensions.zMin; z <= environmentDimensions.zMax; z++) {
                    for (int x = environmentDimensions.xMin; x <= environmentDimensions.xMax; x++)
                    {
                        BlockPos p;
                        if (environmentDimensions.absoluteCoords)
                            p = new BlockPos(x, y, z);
                        else
                            p = pos.add(x, y, z);
                        String name = "";
                        IBlockState state = player.world.getBlockState(p);
                        Object blockName = Block.REGISTRY.getNameForObject(state.getBlock());
                        if (blockName instanceof ResourceLocation) {
                            name = ((ResourceLocation) blockName).getResourcePath();
                        }
                        JsonElement element = new JsonPrimitive(name);
                        arr.add(element);
                    }
                }
            }
        }
        json.add(jsonName, arr);
    }
}
