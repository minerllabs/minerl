package com.microsoft.Malmo.Mixins;

import net.minecraft.client.multiplayer.PlayerControllerMP;
import net.minecraft.entity.Entity;
import net.minecraft.entity.item.EntityMinecartCommandBlock;
import net.minecraft.entity.item.EntityMinecartContainer;
import net.minecraft.entity.passive.EntityVillager;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.util.EnumActionResult;
import net.minecraft.util.EnumHand;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.logging.Level;
import java.util.logging.Logger;

@Mixin(PlayerControllerMP.class)
public abstract class MixinNoGuiEntityInteract {

    /**
     * Disable USE interactions with EntityVillager, MinecartContainers (EntityMinecartChest, EntityMinecartHopper) and EntityMinecartCommandBlock
     * This prevents the server from bing notified that we tried to interact with these entities
     * @param player
     * @param target
     * @param heldItem
     * @param cir
     */
    @SuppressWarnings("AmbiguousMixinReference")
    @Inject(method = "interactWithEntity", at = @At("HEAD"), cancellable = true)
    private void onInteractWithEntity(EntityPlayer player, Entity target, EnumHand heldItem, CallbackInfoReturnable<EnumActionResult> cir) {
        if (target instanceof EntityVillager
            || target instanceof EntityMinecartContainer
            || target instanceof EntityMinecartCommandBlock)
            cir.setReturnValue(EnumActionResult.SUCCESS);
    }

}
