package com.microsoft.Malmo.Utils;

import com.microsoft.Malmo.Schemas.UnnamedGridDefinition;
import net.minecraft.client.Minecraft;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.IThreadListener;
import net.minecraft.world.World;
import net.minecraft.world.WorldServer;
import net.minecraftforge.fml.common.FMLCommonHandler;
import net.minecraftforge.fml.common.eventhandler.Event;
import net.minecraftforge.fml.relauncher.Side;

public class RunLater {
    public static void ToRunLater(Runnable toRun){
        IThreadListener mainThread;
        if (FMLCommonHandler.instance().getSide() == Side.CLIENT) {
            mainThread = Minecraft.getMinecraft();
        } else {
            mainThread = FMLCommonHandler.instance().getMinecraftServerInstance();
        }
        mainThread.addScheduledTask(toRun);
    }
}
