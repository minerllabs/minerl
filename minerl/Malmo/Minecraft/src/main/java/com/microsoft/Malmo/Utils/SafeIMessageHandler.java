package com.microsoft.Malmo.Utils;

import com.microsoft.Malmo.MissionHandlers.NearbySmeltCommandsImplementation;
import net.minecraft.client.Minecraft;
import net.minecraft.util.IThreadListener;
import net.minecraft.world.WorldServer;
import net.minecraftforge.fml.common.network.simpleimpl.IMessage;
import net.minecraftforge.fml.common.network.simpleimpl.IMessageHandler;
import net.minecraftforge.fml.common.network.simpleimpl.MessageContext;
import net.minecraftforge.fml.relauncher.Side;

public abstract class SafeIMessageHandler<REQ extends IMessage, REPLY extends IMessage> implements IMessageHandler<REQ, REPLY> {
    public REPLY onMessage(REQ message, MessageContext ctx){
        IThreadListener mainThread;
        if (ctx.side == Side.CLIENT)
            mainThread = Minecraft.getMinecraft();
        else
            mainThread = (WorldServer)ctx.getServerHandler().playerEntity.world;

        mainThread.addScheduledTask(toRunOnMessage(message, ctx));

        return null;
    }

    public abstract Runnable toRunOnMessage(REQ message, MessageContext ctx);
}
