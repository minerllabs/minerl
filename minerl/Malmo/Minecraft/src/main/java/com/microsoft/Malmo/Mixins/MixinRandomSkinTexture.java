

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
    private static Boolean isSlim = null;
    @Inject(method = "isSlimSkin", at = @At("HEAD"), cancellable = true)
    private static void isSlimSkin(UUID playerUUID, CallbackInfoReturnable<Boolean> cir){
        if (isSlim == null) {
            Random rand = new Random();
            isSlim = rand.nextBoolean();
        }
        cir.setReturnValue(isSlim);
        cir.cancel();
    }
  
}
