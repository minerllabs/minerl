package com.microsoft.Malmo.Mixins;


import net.minecraft.entity.player.InventoryPlayer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.Constant;
import org.spongepowered.asm.mixin.injection.ModifyConstant;


@Mixin(InventoryPlayer.class)
public class MixinLargeInventory  {
    // /* Overrides default inventory size within the InventoryPlayer class.
    //  */

    @ModifyConstant(method = "<init>", constant = @Constant(intValue = 36))
    private static int modifyMainInventorySize() {
        return 360;
    }
}
