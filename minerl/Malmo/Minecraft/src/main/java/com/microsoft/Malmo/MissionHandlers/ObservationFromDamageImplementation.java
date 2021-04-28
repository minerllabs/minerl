package com.microsoft.Malmo.MissionHandlers;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import com.microsoft.Malmo.MissionHandlerInterfaces.IObservationProducer;
import com.microsoft.Malmo.Schemas.MissionInit;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.entity.EntityList;
import net.minecraft.entity.EntityLivingBase;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.item.ItemStack;
import net.minecraft.util.DamageSource;
import net.minecraft.util.math.Vec3d;
import net.minecraftforge.common.ForgeHooks;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.living.LivingEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.fml.common.eventhandler.Cancelable;
import net.minecraftforge.fml.common.eventhandler.Event;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;
import net.minecraftforge.fml.common.registry.EntityRegistry;


import java.util.Arrays;
import java.util.List;

import static java.lang.Math.*;

/**
 * Simple IObservationProducer object that records the damage taken by an agent.<br>
 */
public class ObservationFromDamageImplementation extends HandlerBase implements IObservationProducer
{
    private DamageSource damageSource;
    private float damageAmount;

    public List<String> DamageTypeKeys = Arrays.asList(
            "none",
            "inFire",
            "lightningBolt",
            "onFire",
            "lava",
            "hotFloor",
            "inWall",
            "cramming",
            "drown",
            "starve",
            "cactus",
            "fall",
            "flyIntoWall",
            "outOfWorld",
            "generic",
            "magic",
            "wither",
            "anvil",
            "fallingBlock",
            "dragonBreath",
            "fireworks",
            "mob",
            "player",
            "arrow",
            "fireball",
            "thrown",
            "indirectMagic",
            "thorns",
            "explosion.player",
            "other");


    @Override
    public void prepare(MissionInit missionInit) {}

    @Override
    public void cleanup() {}

    /**
     * LivingHurtEvent is fired when an Entity is set to be hurt. <br>
     * This event is fired whenever an Entity is hurt in
     * {@link EntityLivingBase#damageEntity(DamageSource, float)} and
     * {@link EntityPlayer#damageEntity(DamageSource, float)}.<br>
     * <br>
     * This event is fired via the {@link ForgeHooks#onLivingHurt(EntityLivingBase, DamageSource, float)}.<br>
     * <br>
     * {@link #source} contains the DamageSource that caused this Entity to be hurt. <br>
     * {@link #amount} contains the amount of damage dealt to the Entity that was hurt. <br>
     * <br>
     * This event is {@link Cancelable}.<br>
     * If this event is canceled, the Entity is not hurt.<br>
     * <br>
     * This event does not have a result. {@link Event.HasResult}<br>
     * <br>
     * This event is fired on the {@link MinecraftForge#EVENT_BUS}.
     **/
    @SubscribeEvent()
    public void onClientTick(LivingHurtEvent event)
    {
        if (event.getEntity().equals(Minecraft.getMinecraft().player)) {
            this.damageSource = event.getSource();
            this.damageAmount = event.getAmount();
        }
    }

    @Override
    public void writeObservationsToJSON(JsonObject json, MissionInit missionInit)
    {
        EntityPlayerSP player = Minecraft.getMinecraft().player;
        JsonObject death_json = new JsonObject();
        json.addProperty("is_dead", player.isDead);

        if (this.damageSource != null) {
            death_json.addProperty("damage_amount", this.damageAmount);
            death_json.addProperty("damage_type", this.damageSource.getDamageType());
            death_json.addProperty("damage_type_enum",
                    DamageTypeKeys.contains(this.damageSource.getDamageType())
                            ? DamageTypeKeys.indexOf(this.damageSource.getDamageType())
                            : DamageTypeKeys.indexOf("other"));
            death_json.addProperty("hunger_damage", this.damageSource.getHungerDamage());
            death_json.addProperty("is_damage_absolute", this.damageSource.isDamageAbsolute() ? 1 : 0);
            death_json.addProperty("is_fire_damage", this.damageSource.isFireDamage() ? 1 : 0);
            death_json.addProperty("is_magic_damage", this.damageSource.isMagicDamage() ? 1 : 0);
            death_json.addProperty("is_difficulty_scaled", this.damageSource.isDifficultyScaled() ? 1 : 0);
            death_json.addProperty("is_explosion", this.damageSource.isExplosion() ? 1 : 0);
            death_json.addProperty("is_projectile", this.damageSource.isProjectile() ? 1 : 0);
            death_json.addProperty("is_unblockable", this.damageSource.isUnblockable() ? 1 : 0);
            death_json.addProperty("death_message", this.damageSource.getDeathMessage(player).getUnformattedText());

            if (this.damageSource.getEntity() != null) {
                death_json.addProperty("damage_entity", this.damageSource.getEntity().getName());
                death_json.addProperty("damage_entity_registry_id",
                        (this.damageSource.getEntity() != null
                        && EntityRegistry.getEntry(this.damageSource.getEntity().getClass()) != null)
                                ? EntityList.getID(this.damageSource.getEntity().getClass()) : 0);
                death_json.addProperty("damage_entity_id", this.damageSource.getEntity().getEntityId());
                death_json.addProperty("damage_entity_uuid", String.valueOf(this.damageSource.getEntity().getPersistentID()));

                JsonArray entity_equipment = new JsonArray();
                // TODO do we need to mark the equipment slot of this armor?
                for (ItemStack item : this.damageSource.getEntity().getEquipmentAndArmor()) {
                    if (item.getItem().getRegistryName() != null) {
                        JsonElement jitem = new JsonPrimitive(item.getItem().getRegistryName().toString());
                        entity_equipment.add(jitem);
                    }
                }
                death_json.add("damage_entity_equipment", entity_equipment);
            }

            if (this.damageSource.getDamageLocation() != null) {
                death_json.addProperty("damage_location", this.damageSource.getDamageLocation().toString());
                death_json.addProperty("damage_location_x", this.damageSource.getDamageLocation().xCoord);
                death_json.addProperty("damage_location_y", this.damageSource.getDamageLocation().yCoord);
                death_json.addProperty("damage_location_z", this.damageSource.getDamageLocation().zCoord);
                death_json.addProperty("damage_relative_distance", this.damageSource.getDamageLocation().distanceTo(player.getPositionVector()));
                Vec3d attack_vec = this.damageSource.getDamageLocation().subtract(player.getPositionVector());
                death_json.addProperty("damage_pitch", asin(attack_vec.yCoord));
                death_json.addProperty("damage_yaw", atan2(attack_vec.xCoord, attack_vec.zCoord));
            }
            this.damageSource = null;
        }

        json.add("damage_source", death_json);
    }

}