package com.microsoft.Malmo.MissionHandlers;

import com.google.gson.JsonObject;
import com.microsoft.Malmo.MissionHandlerInterfaces.IObservationProducer;
import com.microsoft.Malmo.Schemas.DrawItem;
import com.microsoft.Malmo.Schemas.MissionInit;
import com.microsoft.Malmo.Utils.MinecraftTypeHelper;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.inventory.EntityEquipmentSlot;
import net.minecraft.item.ItemStack;
import net.minecraft.util.DamageSource;

/**
 * Simple IObservationProducer object that pings out a whole bunch of data.<br>
 */
public class ObservationFromCauseOfDeathImplementation extends HandlerBase implements IObservationProducer
{
    private DamageSource damageSource;


	@Override
	public void prepare(MissionInit missionInit) {}

	@Override
	public void cleanup() {}

	@Override
    public void writeObservationsToJSON(JsonObject json, MissionInit missionInit)
    {
        EntityPlayerSP player = Minecraft.getMinecraft().player;
        JsonObject death_json = new JsonObject();
        death_json.addProperty("is_dead", player.isDead);

        if (player.isDead) {
            death_json.addProperty("damage_source",1);
        }

        json.add("cause_of_death", death_json);
    }

}