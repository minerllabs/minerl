

package com.microsoft.Malmo.Mixins;


import java.util.Random;
import java.util.UUID;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.client.resources.DefaultPlayerSkin;


@Mixin(DefaultPlayerSkin.class)
public abstract class MixinRandomSkinTexture {
    // Randomize the skin for agents ignoring UUID
    private static Integer skinSeed = null;
    @Inject(method = "isSlimSkin", at = @At("HEAD"), cancellable = true)
    private static void isSlimSkin(UUID playerUUID, CallbackInfoReturnable<Boolean> cir){
        if (skinSeed == null) {
            // TODO now this is not blinking, and randomized, but not consistent between
            // clients. Ideally, we should somehow sync this between clients -
            // is there any pseudo-random number in the minecraft world we
            // could base this on?
            Random rand = new Random();
            skinSeed = rand.nextInt();
        }
        cir.setReturnValue(((playerUUID.hashCode() + skinSeed) & 1) == 0);
        cir.cancel();
    }
  
}
