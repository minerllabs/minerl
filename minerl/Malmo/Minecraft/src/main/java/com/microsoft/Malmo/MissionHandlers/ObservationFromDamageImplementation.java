package com.microsoft.Malmo.MissionHandlers;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import com.microsoft.Malmo.MissionHandlerInterfaces.IObservationProducer;
import com.microsoft.Malmo.Schemas.MissionInit;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityLivingBase;
import net.minecraft.item.ItemStack;
import net.minecraft.util.DamageSource;
import net.minecraft.util.math.Vec3d;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;


import static java.lang.Math.*;

/**
 * Simple IObservationProducer object that pings out a whole bunch of data.<br>
 */
public class ObservationFromDamageImplementation extends HandlerBase implements IObservationProducer
{
    private DamageSource damageSource;
    private float damageAmount;
    private EntityLivingBase entity;
    private boolean hasDied = false;


	@Override
	public void prepare(MissionInit missionInit) {
        MinecraftForge.EVENT_BUS.register(this);
    }

	@Override
	public void cleanup() {}

    @SubscribeEvent
    public void onClientTick(LivingDeathEvent event)
    {
        if (event.getEntityLiving().equals(Minecraft.getMinecraft().player)) {
            if (this.damageSource != null) {
                System.out.println("Warning overwriting damage source - entity has died!");
            }
            this.damageSource = event.getSource();
            this.entity = event.getEntityLiving();
            this.hasDied = true;
        }
    }
    
    @SubscribeEvent
    public void onDamage(LivingHurtEvent event)
    {
        if (event.getEntityLiving().equals(Minecraft.getMinecraft().player)) {
            if (this.damageSource != null) {
                System.out.println("Warning skipped damage event - multiple damage events in one tick!");
            }
            this.damageSource = event.getSource();
            this.damageAmount = event.getAmount();
            this.entity = event.getEntityLiving();
        }
    }

    private void resetDamage(){
	    this.damageAmount = 0;
	    this.damageSource = null;
	    this.entity = null;
	    this.hasDied = false;
    }

	@Override
    public void writeObservationsToJSON(JsonObject json, MissionInit missionInit)
    {
        EntityPlayerSP player = Minecraft.getMinecraft().player;
        JsonObject damage_json = new JsonObject();
        json.addProperty("is_dead", player.isDead);
        json.addProperty("living_death_event_fired", this.hasDied);
        this.hasDied = false;
        
        if (this.damageAmount != 0 && this.damageSource != null) {
            System.out.println(this.damageAmount + " damage from " + this.damageSource.getDamageType() + " by entity " + this.damageSource.getEntity());
        }

        if (this.damageAmount != 0) {
            damage_json.addProperty("damage_amount", this.damageAmount);
        }

        if (this.damageSource != null) {
            damage_json.addProperty("damage_type", this.damageSource.getDamageType());
            damage_json.addProperty("hunger_damage", this.damageSource.getHungerDamage());
            damage_json.addProperty("is_damage_absolute", this.damageSource.isDamageAbsolute());
            damage_json.addProperty("is_fire_damage", this.damageSource.isFireDamage());
            damage_json.addProperty("is_magic_damage", this.damageSource.isMagicDamage());
            damage_json.addProperty("is_difficulty_scaled", this.damageSource.isDifficultyScaled());
            damage_json.addProperty("is_explosion", this.damageSource.isExplosion());
            damage_json.addProperty("is_projectile", this.damageSource.isProjectile());
            damage_json.addProperty("is_unblockable", this.damageSource.isUnblockable());
            damage_json.addProperty("death_message", this.damageSource.getDeathMessage(player).getUnformattedText());

            if (this.damageSource.getEntity() != null) {
                damage_json.addProperty("damage_entity", this.damageSource.getEntity().getName());
                damage_json.addProperty("damage_entity_id", this.damageSource.getEntity().getEntityId());
                JsonArray entity_equipment = new JsonArray();
                // TODO do we need to mark the equipment slot of this armor?
                for (ItemStack item : this.damageSource.getEntity().getEquipmentAndArmor()) {
                    if (item.getItem().getRegistryName() != null) {
                        JsonElement jitem = new JsonPrimitive(item.getItem().getRegistryName().toString());
                        entity_equipment.add(jitem);
                    }
                }
                damage_json.add("damage_entity_equipment", entity_equipment);
            } if (this.damageSource.getDamageLocation() != null) {
                damage_json.addProperty("damage_location", this.damageSource.getDamageLocation().toString());
                damage_json.addProperty("damage_distance", this.damageSource.getDamageLocation().distanceTo(player.getPositionVector()));
                Vec3d attack_vec = this.damageSource.getDamageLocation().subtract(player.getPositionVector());
                damage_json.addProperty("damage_pitch", asin(attack_vec.yCoord));
                damage_json.addProperty("damage_yaw", atan2(attack_vec.xCoord, attack_vec.zCoord));
            }
        }

        this.resetDamage();

        json.add("damage_source", damage_json);
    }

}