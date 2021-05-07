// --------------------------------------------------------------------------------------------------
//  Copyright (c) 2016 Microsoft Corporation
//  
//  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
//  associated documentation files (the "Software"), to deal in the Software without restriction,
//  including without limitation the rights to use, copy, modify, merge, publish, distribute,
//  sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
//  furnished to do so, subject to the following conditions:
//  
//  The above copyright notice and this permission notice shall be included in all copies or
//  substantial portions of the Software.
//  
//  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
//  NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
//  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
//  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
// --------------------------------------------------------------------------------------------------

package com.microsoft.Malmo.Utils;

import java.lang.reflect.Field;
import java.util.concurrent.locks.ReentrantLock;

import net.minecraft.client.Minecraft;
import net.minecraft.launchwrapper.Launch;
import net.minecraft.util.Timer;
import net.minecraft.world.World;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.common.eventhandler.Event;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;
import net.minecraftforge.fml.common.gameevent.TickEvent;
import net.minecraftforge.fml.common.gameevent.TickEvent.ClientTickEvent;
import net.minecraftforge.fml.common.gameevent.TickEvent.Phase;
import net.minecraftforge.fml.relauncher.Side;

/** Time-based methods and helpers.<br>
 * Time is usually measured in some form of game tick (eg WorldTick etc). In the normal course of operations,
 * these take places 20 times a second - hence a MillisencondsPerWorldTick value of 50.
 * If the game is overclocked, this is no longer true, but generally it still makes sense to deal with a simple multiple of game ticks,
 * so we leave MillisecondsPerWorldTick unchanged.
 */

@Mod.EventBusSubscriber
public class TimeHelper
{
    public final static float MillisecondsPerWorldTick = 50.0f;
    public final static float MillisecondsPerSecond = 1000.0f;
    private static Boolean paused = false;  //If ticking should be paused.
    public static long serverTickLength = 50;
    public static long displayGranularityMs = 50;  // How quickly we allow the Minecraft window to update.
    private static long lastUpdateTimeMs;
    public static int frameSkip = 1; // Note: Not fully implemented
    public static Boolean isWindows = System.getProperty("os.name").startsWith("Windows");

    static public class FlushableStateMachine {
        // We should really just use locks.
        boolean executing = false;
        boolean shouldFlush = false;
        boolean completed = true;
        ReentrantLock lock = new ReentrantLock();
        ReentrantLock requestLock = new ReentrantLock();
        String name = "";

        public FlushableStateMachine(String name) {
            this.name = name;
        }
        
        public boolean request(){
            lock.lock();
            try {
                if(completed){
                    // ONLY EXECUTE ON SYNCHRONOUS MODE
                    // SyncManager.debugLog("[FSM:" + name + "] REQUEST SENT");
                    completed = false;
                    executing = true;
                    return true;
                } 
                // OTHERWISE DENY THE REQUEST.
                return false;
            } finally {
                lock.unlock();
            }
        }

        public void complete() {
            lock.lock();
            try {
                // SyncManager.debugLog("[FSM:" + name + "] COMPLETING TICK");
                executing = false;
                completed = true;
            } finally {
                lock.unlock();
            }
        }
        
        
        public void requestAndWait() {
            // This requests the state machine to run and waits for completion.
            requestLock.lock();
            try{
                // if(SyncManager.synchronous) SyncManager.debugLog("[FSM:" + name + "] REQUESTING ");
                while(SyncManager.synchronous && ! this.request() ) { Thread.yield();}
                // if(SyncManager.synchronous) SyncManager.debugLog("[FSM:" + name + "] WAITING FOR COMPLETION ");
                while(SyncManager.synchronous && ! this.completed) { Thread.yield();}
                // if(SyncManager.synchronous) SyncManager.debugLog("[FSM:" + name + "] COMPLETED ");
            } finally {
                requestLock.unlock();
            }
        }

        public void awaitRequest(Boolean updateDisplay) {
            // This waits for someone to request execution.

            // if(SyncManager.synchronous) SyncManager.debugLog("[FSM:" + name + "] AWAITING REQUEST ");
            while( SyncManager.synchronous && !this.executing) { 
                if (updateDisplay)
                    TimeHelper.updateDisplay();

                Thread.yield();
            }
            // if(SyncManager.synchronous) SyncManager.debugLog("[FSM:" + name + "] REQUEST RECIEVED STARTING ");
        }
    }
    
    static public class SyncManager {
        static Boolean synchronous = false;
        public static FlushableStateMachine clientTick = new FlushableStateMachine("client");
        public static FlushableStateMachine serverTick = new FlushableStateMachine("server");
        static Boolean serverRunning = false;
        static Boolean serverPistolFired = false;
        public static long numTicks = 0;
        final static Boolean verbose = true;
        public static int role = 0;

        public static synchronized Boolean isSynchronous(){
            return synchronous;
        } 

        public static synchronized  void setSynchronous(Boolean value){
            synchronous = value;
        }
     

        public static synchronized void setPistolFired(Boolean hasIt){
            if(hasIt && !serverPistolFired){
                // TimeHelper.SyncManager.debugLog("Server pistol has started firing.");
            }
            serverPistolFired = hasIt;
        }   


        public static synchronized void debugLog(String logger){
            if(verbose){
                System.out.println("SM: " + logger);
            }
        }


        public static synchronized void setServerRunning(){
            serverRunning = true;
        }

        public static synchronized Boolean isServerRunning(){
            return serverRunning;
        }

        public static synchronized void setServerFinished(){
            serverRunning = false;
        }


        public static synchronized Boolean hasServerFiredPistol(){
            return serverPistolFired;
        }
    }

    static public class  SyncTickEvent extends Event {
        public TickEvent.Phase pos;

        public SyncTickEvent(TickEvent.Phase phaseIn){
            this.pos = phaseIn;
            //We don't need a side since we assume this is 
            // all happening on a single player client with 
            // an integrated server, so the Type of CLIENT =>
            // that the side is CLIENT, as well as the SERVER.
        }
    }

    /** Provide a means to measure the frequency of an event, over a rolling window.
     */
    static public class TickRateMonitor
    {
        long[] eventTimestamps;
        int eventIndex = 0;
        float eventsPerSecond = 0;
        int windowSize = 10;

        public TickRateMonitor()
        {
            this.init(10);
        }

        public TickRateMonitor(int windowSize)
        {
            this.init(windowSize);
        }

        void init(int windowSize)
        {
            this.windowSize = windowSize;
            this.eventTimestamps = new long[this.windowSize];
        }

        public float getEventsPerSecond()
        {
            return this.eventsPerSecond;
        }

        public void beat()
        {
            this.eventIndex = (this.eventIndex + 1) % this.windowSize;
            long then = this.eventTimestamps[this.eventIndex];
            long now = System.currentTimeMillis();
            this.eventTimestamps[this.eventIndex] = now;
            if (then == now)
            {
                System.out.println("Warning: window too narrow for timing events - increase window, or call beat() less often.");
            }
            this.eventsPerSecond = 1000.0f * (float) this.windowSize / (float) (now - then);
        }
    }

    /** Very simple stopwatch-style timer class; times in WorldTicks.
     */
    static public class WorldTimer
    {
        private World world;
        private long startTime = 0;
        private long stopTime = 0;
        
        public WorldTimer(World world)
        {
            this.world = world;
        }
        
        /** Start timing
         */
        public void start()
        {
            this.startTime = this.world.getTotalWorldTime();
            this.stopTime = 0;
        }
        
        /** Stop timing
         */
        public void stop()
        {
            this.stopTime = this.world.getTotalWorldTime();
        }
        
        /** Get the timed duration, converted into what would be milliseconds if no over-clocking has occurred.<br>
         * If stop() has been called, returns the time between calls to stop() and start().
         * If start() has been called but not stop, returns the time since start() was called.<br>
         * It is up to the user to avoid doing things in a stupid order.
         * @return the measured duration
         */
        public float getDurationInMs()
        {
            long duration = (stopTime != 0) ? this.stopTime - this.startTime : this.world.getTotalWorldTime() - this.startTime;
            return duration * MillisecondsPerWorldTick;
        }
    }
    
    static public boolean setMinecraftClientClockSpeed(float ticksPerSecond)
    {
        // * NOTE: In Minecraft 1.12 this changes; tickLength is the main mechanism 
        // for advancing ticks.
        Minecraft.getMinecraft().timer = new PauseTimer( new Timer(ticksPerSecond));
        
        return false;
    }

    static public void pause(){
        System.out.println("Pausing");
        paused = true;
    }
    
    @SubscribeEvent
    public static  void pauseClientTickHander(ClientTickEvent e){
        if(e.phase == Phase.START){
            Minecraft.getMinecraft().isGamePaused = paused || Minecraft.getMinecraft().isGamePaused();
        }
    }

    @SubscribeEvent
    public static void unpauseOnShutdown(net.minecraftforge.event.world.WorldEvent.Unload e){
        SyncManager.setSynchronous(false);
        unpause();
    }

    static public void unpause(){
        System.out.println("Unpausing");
        paused = false;
    }

    static public Boolean isPaused(){
        return paused;
    }
    static public void updateDisplay()
    {
        long timeNow = System.currentTimeMillis();        
        if(lastUpdateTimeMs == -1)
            lastUpdateTimeMs = timeNow;
        
        // Do not update display on Windows at all.
        // Doing so will reset the observation data we get (camera is zeros),
        // and also blinks the Minecraft window between visible frame and black image.

        // This has the side-effect of Minecraft window being blank and
        // reported as "not responding".
        // TODO what is the real cause behind the issues
        if (!isWindows && timeNow - lastUpdateTimeMs > displayGranularityMs)
        {
            Minecraft.getMinecraft().updateDisplay();
            lastUpdateTimeMs = timeNow;
        }
    }
}