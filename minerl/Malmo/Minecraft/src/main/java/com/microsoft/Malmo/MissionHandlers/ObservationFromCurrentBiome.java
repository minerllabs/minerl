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

import com.google.gson.JsonObject;
import com.microsoft.Malmo.MissionHandlerInterfaces.IObservationProducer;
import com.microsoft.Malmo.Schemas.MissionInit;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityLivingBase;
import net.minecraft.entity.item.EntityItemFrame;
import net.minecraft.entity.player.InventoryPlayer;
import net.minecraft.item.IItemPropertyGetter;
import net.minecraft.item.ItemCompass;
import net.minecraft.item.ItemStack;
import net.minecraft.util.ResourceLocation;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.MathHelper;
import net.minecraft.world.World;
import net.minecraft.world.biome.Biome;
import net.minecraftforge.fml.relauncher.Side;
import net.minecraftforge.fml.relauncher.SideOnly;

import javax.annotation.Nullable;


/**
 * Creates observations from the agent's current biome.
 * Could be extended to include other local properties such as light-level, weather, etc.
 * 
 * @author Brandon Houghton
 */
public class ObservationFromCurrentBiome extends HandlerBase implements IObservationProducer {
	boolean compassSet = false;

	@Override
	public void writeObservationsToJSON(JsonObject baseJson, MissionInit missionInit) {
		EntityPlayerSP player = Minecraft.getMinecraft().player;
		JsonObject biomeJson = new JsonObject();

		if (player == null || player.world == null)
			return;

		BlockPos playerPos = player.getPosition();
		Biome playerBiome = player.world.getBiome(playerPos);
		// Name of the current biome
		biomeJson.addProperty("biome_name", playerBiome.getBiomeName());
		// ID of the current biome
		biomeJson.addProperty("biome_id", Biome.getIdForBiome(playerBiome));
		// The average temperature of the current biome
		biomeJson.addProperty("biome_temperature", playerBiome.getTemperature());
		// The average rainfall chance of the current biome
		biomeJson.addProperty("biome_rainfall", playerBiome.getRainfall());
		// [0. 14] The current combined light level of the current player pos
		biomeJson.addProperty("light_level", player.world.getLight(playerPos));
		// If the playerPos has LOS to the sky
		biomeJson.addProperty("can_see_sky", player.world.canSeeSky(playerPos));
		// [0, 1] Brightness factor of the sun
		biomeJson.addProperty("sun_brightness", player.world.getSunBrightnessFactor(0));
		// [0, 14] Light level provided by the sky
		biomeJson.addProperty("sky_light_level", player.world.getSunBrightness(0));
		// TODO add other statuses such as current weather

		baseJson.add("current_biome", biomeJson);
	}

	@Override
	public void prepare(MissionInit missionInit) {

	}

	@Override
	public void cleanup() {

	}
}
