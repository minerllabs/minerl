package com.microsoft.Malmo.MissionHandlers;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import com.microsoft.Malmo.MissionHandlerInterfaces.IObservationProducer;
import com.microsoft.Malmo.Schemas.MissionInit;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.item.ItemStack;
import net.minecraft.util.DamageSource;
import net.minecraft.util.math.Vec3d;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;


import static java.lang.Math.*;

/**
 * Simple IObservationProducer object that pings out a whole bunch of data.<br>
 */
public class ObservationFromDamageImplementation extends HandlerBase implements IObservationProducer
{
    private DamageSource damageSource;


	@Override
	public void prepare(MissionInit missionInit) {}

	@Override
	public void cleanup() {}

    @SubscribeEvent()
    public void onClientTick(LivingDeathEvent event)
    {
        // Use the client tick to ensure we regularly update our state (from the client thread)
        this.damageSource = event.getSource();
    }

	@Override
    public void writeObservationsToJSON(JsonObject json, MissionInit missionInit)
    {
        EntityPlayerSP player = Minecraft.getMinecraft().player;
        JsonObject death_json = new JsonObject();
        json.addProperty("is_dead", player.isDead);

        if (this.damageSource != null) {
            death_json.addProperty("damage_source", this.damageSource.getDamageType());
            death_json.addProperty("hunger_damage", this.damageSource.getHungerDamage());
            death_json.addProperty("is_damage_absolute", this.damageSource.isDamageAbsolute());
            death_json.addProperty("is_fire_damage", this.damageSource.isFireDamage());
            death_json.addProperty("is_magic_damage", this.damageSource.isMagicDamage());
            death_json.addProperty("is_difficulty_scaled", this.damageSource.isDifficultyScaled());
            death_json.addProperty("is_explosion", this.damageSource.isExplosion());
            death_json.addProperty("is_projectile", this.damageSource.isProjectile());
            death_json.addProperty("is_unblockable", this.damageSource.isUnblockable());
            death_json.addProperty("death_message", this.damageSource.getDeathMessage(player).getUnformattedText());

            if (this.damageSource.getEntity() != null) {
                death_json.addProperty("damage_entity", this.damageSource.getEntity().getName());
                death_json.addProperty("damage_entity_id", this.damageSource.getEntity().getEntityId());
                JsonArray entity_equipment = new JsonArray();
                // TODO do we need to mark the equipment slot of this armor?
                for (ItemStack item : this.damageSource.getEntity().getEquipmentAndArmor()) {
                    if (item.getItem().getRegistryName() != null) {
                        JsonElement jitem = new JsonPrimitive(item.getItem().getRegistryName().toString());
                        entity_equipment.add(jitem);
                    }
                }
                death_json.add("damage_entity_equipment", entity_equipment);
            } if (this.damageSource.getDamageLocation() != null) {
                death_json.addProperty("damage_location", this.damageSource.getDamageLocation().toString());
                death_json.addProperty("damage_distance", this.damageSource.getDamageLocation().distanceTo(player.getPositionVector()));
                Vec3d attack_vec = this.damageSource.getDamageLocation().subtract(player.getPositionVector());
                death_json.addProperty("damage_pitch", asin(attack_vec.yCoord));
                death_json.addProperty("damage_yaw", atan2(attack_vec.xCoord, attack_vec.zCoord));
            }
            this.damageSource = null;
        }

        json.add("damage_source", death_json);
    }

}