package com.microsoft.Malmo.Mixins;

import org.lwjgl.input.Mouse;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Overwrite;

import com.microsoft.Malmo.Client.FakeMouse;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(Mouse.class)
public abstract class MixinMouse {

    private static boolean mouseNext = false;


    @Inject(at = @At("HEAD"), method = "setGrabbed", remap = false, cancellable = true)
    private static void setGrabbed(boolean grabbed, CallbackInfo ci) {
        FakeMouse.setGrabbed(grabbed);
        if (!FakeMouse.isHumanInput()) {
            ci.cancel();;
        }
    }

    @Overwrite(remap = false)
    public static boolean isGrabbed() {
        return FakeMouse.isGrabbed();
    }



    @Inject(at = @At("HEAD"), method = "getX", remap = false, cancellable = true)
    private static void getX(CallbackInfoReturnable<Integer> cir) {
        cir.setReturnValue(FakeMouse.getX());
    }

    @Inject(at = @At("HEAD"), method = "getY", remap = false, cancellable = true)
    private static void getY(CallbackInfoReturnable<Integer> cir) {
        cir.setReturnValue(FakeMouse.getY());
    }

    @Inject(at = @At("HEAD"), method = "getDX", remap = false, cancellable = true)
    private static void getDX(CallbackInfoReturnable<Integer> cir) {
        cir.setReturnValue(FakeMouse.getDX());
    }

    @Inject(at = @At("HEAD"), method = "getDY", remap = false, cancellable = true)
    private static void getDY(CallbackInfoReturnable<Integer> cir) {
        cir.setReturnValue(FakeMouse.getDY());
    }

    @Inject(at = @At("HEAD"), method = "getDWheel", remap = false, cancellable = true)
    private static void getDWheel(CallbackInfoReturnable<Integer> cir) {
        cir.setReturnValue(FakeMouse.getDWheel());
    }

    @Inject(at = @At("HEAD"), method = "isButtonDown", remap = false, cancellable = true)
    private static void isButtonDown(int button, CallbackInfoReturnable<Boolean> cir) {
        cir.setReturnValue(FakeMouse.isButtonDown(button));
    }

    @Inject(at = @At("RETURN"), method = "next", remap = false, cancellable = true)
    private static void next(CallbackInfoReturnable<Boolean> cir) {
        // mouseNext is a flag specifying that next read operation should be directly
        // from mouse (instead of FakeMouse).
        // Thread safety of such arrangement is questionable
        mouseNext = cir.getReturnValue();
        if (mouseNext && FakeMouse.isHumanInput()) {
            FakeMouse.addEvent(new FakeMouse.FakeMouseEvent(Mouse.getEventX(), Mouse.getEventY(), Mouse.getEventDX(), Mouse.getEventDY(), Mouse.getEventDWheel(), Mouse.getEventButton(), Mouse.getEventButtonState(), Mouse.getEventNanoseconds()));
            mouseNext = false;
        }
        cir.setReturnValue(FakeMouse.next());
    }


    @Inject(at = @At("HEAD"), method = "getEventButton", remap = false, cancellable = true)
    private static void getEventButton(CallbackInfoReturnable<Integer> cir) {
        if (!mouseNext) {
            cir.setReturnValue(FakeMouse.getEventButton());
        }
    }

    @Inject(at = @At("HEAD"), method = "getEventButtonState", remap = false, cancellable = true)
    private static void getEventButtonState(CallbackInfoReturnable<Boolean> cir) {
        if (!mouseNext) {
            cir.setReturnValue(FakeMouse.getEventButtonState());
        }
    }

    @Inject(at = @At("HEAD"), method = "getEventX", remap = false, cancellable = true)
    private static void getEventX(CallbackInfoReturnable<Integer> cir) {
        if (!mouseNext) {
            cir.setReturnValue(FakeMouse.getEventX());
        }
    }

    @Inject(at = @At("HEAD"), method = "getEventY", remap = false, cancellable = true)
    private static void getEventY(CallbackInfoReturnable<Integer> cir) {
        if (!mouseNext) {
            cir.setReturnValue(FakeMouse.getEventY());
        }
    }

    @Inject(at = @At("HEAD"), method = "getEventDX", remap = false, cancellable = true)
    private static void getEventDX(CallbackInfoReturnable<Integer> cir) {
        if (!mouseNext) {
            cir.setReturnValue(FakeMouse.getEventDX());
        }
    }

    @Inject(at = @At("HEAD"), method = "getEventDY", remap = false, cancellable = true)
    private static void getEventDY(CallbackInfoReturnable<Integer> cir) {
        if (!mouseNext) {
            cir.setReturnValue(FakeMouse.getEventDY());
        }
    }

    @Inject(at = @At("HEAD"), method = "getEventDWheel", remap = false, cancellable = true)
    private static void getEventDWheel(CallbackInfoReturnable<Integer> cir) {
        if (!mouseNext) {
            cir.setReturnValue(FakeMouse.getEventDWheel());
        }
    }


    @Inject(at = @At("HEAD"), method = "getEventNanoseconds", remap = false, cancellable = true)
    private static void getEventNanoseconds(CallbackInfoReturnable<Long> cir) {
        if (!mouseNext) {
            cir.setReturnValue(FakeMouse.getEventNanoseconds());
        }
    }

/*
    @Overwrite(remap = false)
    public static boolean isInsideWindow() {
        return FakeMouse.isInsideWindow();
    }
*/
    @Inject(at = @At("HEAD"), method = "setCursorPosition", remap = false, cancellable = true)
    private static void setCursorPosition(int newX, int newY, CallbackInfo ci) {
        FakeMouse.setCursorPosition(newX, newY);
        if (!FakeMouse.isHumanInput()) {
            ci.cancel();
        }
    }



}
