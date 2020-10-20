

package com.microsoft.Malmo.Mixins;


import com.microsoft.Malmo.Utils.SeedHelper;
import net.minecraft.client.resources.DefaultPlayerSkin;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.Random;
import java.util.UUID;


@Mixin(DefaultPlayerSkin.class)
public abstract class MixinRandomSkinTexture {
    // Randomize the skin for agents ignoring UUID
    @Inject(method = "isSlimSkin", at = @At("HEAD"), cancellable = true)
    private static void isSlimSkin(UUID playerUUID, CallbackInfoReturnable<Boolean> cir){
        Random rand = new Random();
        cir.setReturnValue(rand.nextBoolean());
        cir.cancel();
    }
  
}
