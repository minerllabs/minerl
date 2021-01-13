package com.microsoft.Malmo.Mixins;

import com.microsoft.Malmo.Client.FakeMouse;
import org.lwjgl.input.Keyboard;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Overwrite;

import com.microsoft.Malmo.Client.FakeKeyboard;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(Keyboard.class)
public abstract class MixinKeyboard {

    private static boolean keyboardNext = false;

    // @Inject(at = @At("HEAD"), method = "isCreated", remap = false, cancellable = true)
    private static void isCreated(CallbackInfoReturnable<Boolean> cir) {
        if (!FakeKeyboard.isHumanInput()) {
            cir.setReturnValue(true);
        }
    }

    // @Inject(at = @At("HEAD"), method = "poll", remap = false, cancellable = true)
    private static void poll(CallbackInfo ci) {
        if (!FakeKeyboard.isHumanInput()) {
            ci.cancel();
        }
    }

    @Inject(at = @At("HEAD"), method = "isKeyDown", remap = false, cancellable = true)
    private static void isKeyDown(int key, CallbackInfoReturnable<Boolean> cir) {
        cir.setReturnValue(FakeKeyboard.isKeyDown(key));
    }

    @Inject(at = @At("RETURN"), method = "next", remap = false, cancellable = true)
    private static void next(CallbackInfoReturnable<Boolean> cir) {
        keyboardNext = cir.getReturnValue();
        if (keyboardNext && FakeKeyboard.isHumanInput()) {
            FakeKeyboard.add(new FakeKeyboard.FakeKeyEvent(Keyboard.getEventCharacter(), Keyboard.getEventKey(), Keyboard.getEventKeyState(), Keyboard.getEventNanoseconds(), Keyboard.isRepeatEvent()));
            keyboardNext = false;
        }
        cir.setReturnValue(FakeKeyboard.next());
    }

    @Inject(at = @At("HEAD"), method = "getEventKey", remap = false, cancellable = true)
    private static void getEventKey(CallbackInfoReturnable<Integer> cir) {
        if (!keyboardNext) {
            cir.setReturnValue(FakeKeyboard.getEventKey());
        }
    }

    @Inject(at = @At("HEAD"), method = "getEventCharacter", remap = false, cancellable = true)
    private static void getEventCharacter(CallbackInfoReturnable<Character> cir) {
        if (!keyboardNext) {
            cir.setReturnValue(FakeKeyboard.getEventCharacter());
        }
    }

    @Inject(at = @At("HEAD"), method = "getEventKeyState", remap = false, cancellable = true)
    private static void getEventKeyState(CallbackInfoReturnable<Boolean> cir) {
        if (!keyboardNext) {
            cir.setReturnValue(FakeKeyboard.getEventKeyState());
        }
    }

    @Inject(at = @At("HEAD"), method = "getEventNanoseconds", remap = false, cancellable = true)
    private static void getEventNanoseconds(CallbackInfoReturnable<Long> cir) {
        if (!keyboardNext) {
            cir.setReturnValue(FakeKeyboard.getEventNanoseconds());
        }
    }

    @Inject(at = @At("HEAD"), method = "isRepeatEvent", remap = false, cancellable = true)
    private static void isRepeatEvent(CallbackInfoReturnable<Boolean> cir) {
        if (!keyboardNext) {
            cir.setReturnValue(FakeKeyboard.isRepeatEvent());
        }
    }
}
