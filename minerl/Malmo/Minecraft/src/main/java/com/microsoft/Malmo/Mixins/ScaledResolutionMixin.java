package com.microsoft.Malmo.Mixins;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.ScaledResolution;
import net.minecraft.util.math.MathHelper;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Overwrite;

@Mixin(ScaledResolution.class)
public abstract class ScaledResolutionMixin {
    private double scaledWidthD;
    private double scaledHeightD;
    private int scaledWidth;
    private int scaledHeight;
    private int scaleFactor;

    private void computeScale() {
        Minecraft minecraftClient = Minecraft.getMinecraft();
        this.scaledWidth = minecraftClient.displayWidth;
        this.scaledHeight = minecraftClient.displayHeight;
        this.scaleFactor = 1;
        boolean flag = minecraftClient.isUnicode();
        int i = minecraftClient.gameSettings.guiScale;

        if (i == 0)
        {
            i = 1000;
        }

        while (this.scaleFactor < i && this.scaledWidth / (this.scaleFactor + 1) >= 320 && this.scaledHeight / (this.scaleFactor + 1) >= 240)
        {
            ++this.scaleFactor;
        }

        if (flag && this.scaleFactor % 2 != 0 && this.scaleFactor != 1)
        {
            --this.scaleFactor;
        }

        this.scaledWidthD = (double)this.scaledWidth / (double)this.scaleFactor;
        this.scaledHeightD = (double)this.scaledHeight / (double)this.scaleFactor;
        this.scaledWidth = MathHelper.ceil(this.scaledWidthD);
        this.scaledHeight = MathHelper.ceil(this.scaledHeightD);
    }

    @Overwrite
    private int getScaledWidth()
    {
        return this.scaledWidth;
    }

    @Overwrite
    private int getScaledHeight()
    {

        return this.scaledHeight;
    }

    @Overwrite
    private double getScaledWidth_double()
    {
        return this.scaledWidthD;
    }

    @Overwrite
    private double getScaledHeight_double()
    {
        return this.scaledHeightD;
    }

    @Overwrite
    private int getScaleFactor()
    {
        return this.scaleFactor;
    }
}
