
package com.microsoft.Malmo.MissionHandlers;


import com.microsoft.Malmo.MissionHandlerInterfaces.IWorldDecorator;
import com.microsoft.Malmo.Schemas.BoundedWorldDecorator;
import com.microsoft.Malmo.Schemas.MissionInit;
import net.minecraft.entity.player.EntityPlayerMP;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;
import net.minecraftforge.event.entity.living.LivingEvent;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class BoundedWorldDecoratorImplementation extends HandlerBase implements IWorldDecorator {
    private float radius;
    private BoundedWorldDecorator params;

    public void parseParameter(Object params){
        if (params == null || !(params instanceof BoundedWorldDecorator))
            return;

        this.params = (BoundedWorldDecorator) params;

        this.radius = this.params.getRadius();
    }

    @SubscribeEvent
    public  void onMove(LivingEvent.LivingUpdateEvent event) {
        if (event.getEntityLiving() != null && event.getEntityLiving() instanceof EntityPlayerMP)
        {


            EntityPlayerMP player = (EntityPlayerMP) event.getEntity();

            BlockPos playerLocation = new BlockPos(player.posX, player.posY + player.getYOffset(), player.posZ);
            float dist = (float) playerLocation.getDistance(0, playerLocation.getY(), 0);
            if( dist > this.radius ){
                BlockPos newPos = new BlockPos(
                        playerLocation.getX()/dist*radius, playerLocation.getY(), playerLocation.getZ()/dist*radius
                );

                player.moveToBlockPosAndAngles(newPos, player.rotationYaw, player.rotationPitch);
            }


        }

    }


    @Override
    public void buildOnWorld(MissionInit missionInit, World world) throws DecoratorException {

    }

    @Override
    public boolean getExtraAgentHandlersAndData(List<Object> handlers, Map<String, String> data) {
        return false;
    }

    @Override
    public void update(World world) {

    }

    @Override
    public void prepare(MissionInit missionInit) {

    }

    @Override
    public void cleanup() {

    }

    @Override
    public boolean targetedUpdate(String nextAgentName) {
        return false;
    }

    @Override
    public void getTurnParticipants(ArrayList<String> participants, ArrayList<Integer> participantSlots) {

    }
}
