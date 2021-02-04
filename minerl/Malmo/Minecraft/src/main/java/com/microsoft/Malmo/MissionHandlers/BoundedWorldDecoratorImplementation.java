
package com.microsoft.Malmo.MissionHandlers;

import com.microsoft.Malmo.MissionHandlerInterfaces.IWorldDecorator;
import com.microsoft.Malmo.Schemas.BoundedWorldDecorator;
import com.microsoft.Malmo.Schemas.MissionInit;
import com.microsoft.Malmo.Utils.PositionHelper;

import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityLivingBase;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.entity.player.EntityPlayerMP;
import net.minecraft.network.play.server.SPacketPlayerPosLook;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.MathHelper;
import net.minecraft.world.World;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.entity.living.LivingEvent;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class BoundedWorldDecoratorImplementation extends HandlerBase implements IWorldDecorator {
    private float radius;
    private BoundedWorldDecorator params;

    @Override
    public boolean parseParameters(Object params){

        if (params == null || !(params instanceof BoundedWorldDecorator))
            return false;

        this.params = (BoundedWorldDecorator) params;

        this.radius = this.params.getRadius();
        return true;

        
    }

    @SubscribeEvent
    public  void onMove(LivingEvent.LivingUpdateEvent event) {
        if (event.getEntityLiving() != null && event.getEntityLiving() instanceof EntityPlayer)
        {
            
            EntityPlayer player = (EntityPlayer) event.getEntity();
            World w = player.world;
            
            int xCoord = w.getSpawnPoint().getX();
            int zCoord = w.getSpawnPoint().getZ();


            BlockPos playerLocation = new BlockPos(player.posX, player.posY, player.posZ);
            System.out.println("CUR_LOCATION:" + playerLocation);
            float dist = (float) playerLocation.getDistance(xCoord, playerLocation.getY(), zCoord);
            System.out.println("SPAWN:" + w.getSpawnPoint());
            System.out.println("DIST: " + dist + " RADIUS: " + radius);
            
            if( dist > this.radius ){
                BlockPos newPos = new BlockPos(
                        (playerLocation.getX()-xCoord)/dist*(radius*.80) + xCoord, playerLocation.getY()+300, (playerLocation.getZ()-zCoord)/dist*(radius*.80) + zCoord
                );
                int height = PositionHelper.getTopSolidOrLiquidBlockFromHeight(w, newPos).getY();
                // Get the highest position above the ground at this sapwn point.
                BlockPos teleportPos = new BlockPos(
                    newPos.getX(), height + 1, newPos.getZ()
                );
                System.out.println("[ERROR] teleport to:" + teleportPos.toString());

                doTeleport(player, teleportPos.getX(), teleportPos.getY(), teleportPos.getZ(), player.rotationYaw, player.rotationPitch);
                // player.moveToBlockPosAndAngles(teleportPos, player.rotationYaw, player.rotationPitch);
                // player.setVelocity(0, 0, 0);
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
    public void prepare(MissionInit missionInit)
    {
        MinecraftForge.EVENT_BUS.register(this);
    }

    @Override
    public void cleanup()
    {
        MinecraftForge.EVENT_BUS.unregister(this);
    }
    
    @Override
    public boolean targetedUpdate(String nextAgentName) {
        return false;
    }

    @Override
    public void getTurnParticipants(ArrayList<String> participants, ArrayList<Integer> participantSlots) {

    }

    private static void doTeleport(Entity p_189862_0_, int x, int y, int z, float yaw, float pitch)
    {
        float f = yaw;
        float f1= pitch;
        if (p_189862_0_ instanceof EntityPlayerMP)
        {
            Set<SPacketPlayerPosLook.EnumFlags> set = EnumSet.<SPacketPlayerPosLook.EnumFlags>noneOf(SPacketPlayerPosLook.EnumFlags.class);

            System.out.println("[ERRROR] SERVER SIDE!");
            p_189862_0_.dismountRidingEntity();
            ((EntityPlayerMP)p_189862_0_).connection.setPlayerLocation(x, y, z, f, f1, set);
            p_189862_0_.setRotationYawHead(f);
        }
        else
        {
            float f2 = (float)MathHelper.wrapDegrees(f);
            float f3 = (float)MathHelper.wrapDegrees(f1);
            f3 = MathHelper.clamp(f3, -90.0F, 90.0F);
            p_189862_0_.setLocationAndAngles(x, y, z, f2, f3);
            p_189862_0_.setRotationYawHead(f2);
        }

        if (!(p_189862_0_ instanceof EntityLivingBase) || !((EntityLivingBase)p_189862_0_).isElytraFlying())
        {
            p_189862_0_.motionY = 0.0D;
            p_189862_0_.onGround = true;
        }
    }

}
