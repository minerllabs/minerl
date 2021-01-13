package com.microsoft.Malmo.Mixins;

import com.microsoft.Malmo.Client.FakeMouse;
import org.lwjgl.opengl.Display;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Overwrite;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(Display.class)
public abstract class MixinDisplay {

    @Inject(at = @At("HEAD"), method = "isActive", remap = false, cancellable = true)
    private static void isActive(CallbackInfoReturnable<Boolean> cir) {
        if (!FakeMouse.isHumanInput()) {
            cir.setReturnValue(true);
        }
    }
}
