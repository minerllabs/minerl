package com.microsoft.Malmo.Client;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.gui.inventory.GuiContainer;
import net.minecraft.client.renderer.GlStateManager;
import net.minecraft.client.renderer.texture.SimpleTexture;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.client.renderer.texture.TextureManager;
import net.minecraft.client.resources.FolderResourcePack;
import net.minecraft.client.resources.IResourceManager;
import net.minecraft.client.resources.IResourcePack;
import net.minecraft.client.resources.SimpleReloadableResourceManager;
import net.minecraft.util.ResourceLocation;
import net.minecraftforge.client.model.ModelLoader;

import java.io.File;
import java.io.IOException;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashSet;
import java.util.Set;

public class FakeMouse {
    private static int x;
    private static int y;
    private static int dx;
    private static int dy;

    private static int accumDx;
    private static int accumDy;


    private static Deque<FakeMouseEvent> eventQueue = new ArrayDeque<FakeMouseEvent>();
    private static FakeMouseEvent currentEvent;
    private static Set<Integer> pressedButtons = new HashSet<Integer>();
    private static Set<Integer> accumPressedButtons = new HashSet<Integer>();

    private static boolean grabbed = false;
    private static boolean humanInput = true;

    private static FakeMouseCursor cursor = new FakeMouseCursor();

    public static void setXFromMouse(int x) {
        if (humanInput) {
            FakeMouse.x = x;
        }
    }

    public static void setYFromMouse(int y) {
        if (humanInput) {
            FakeMouse.y = y;
        }
    }

    public static void setHumanInput(boolean humanInput) {
        FakeMouse.humanInput = humanInput;
    }

    public static boolean isHumanInput() {
        return humanInput;
    }

    public static JsonElement getState() {
        JsonObject retVal = new JsonObject();
        retVal.addProperty("x", x);
        retVal.addProperty("y", y);
        retVal.addProperty("dx", accumDx);
        retVal.addProperty("dy", accumDy);
        retVal.add("buttons", new Gson().toJsonTree(FakeMouse.accumPressedButtons.toArray()));
        System.out.println("get fake mouse state returns " + retVal);
        accumPressedButtons.clear();
        accumDx = 0;
        accumDy = 0;
        return retVal;
    }

    public static void setDXFromMouse(Integer dx) {
        if (humanInput) {
            FakeMouse.dx = dx;
            FakeMouse.accumDx += dx;
        }
    }

    public static void setDYFromMouse(Integer dy) {
        if (humanInput) {
            FakeMouse.dy = dy;
            FakeMouse.accumDy += dy;
        }
    }

    public static void setButtonFromMouse(int button, Boolean down) {
        if (humanInput) {
            if (down) {
                pressButton(button);
            } else {
                releaseButton(button);
            }
        }
    }

    public static class FakeMouseEvent {
        private int button;

        private boolean state;

        private int dx;
        private int dy;
        private int dwheel;

        private int x;
        private int y;
        private long nanos;

        public FakeMouseEvent(int x, int y, int dx, int dy, int dwheel, int button, boolean state, long nanos) {
            this.x = x;
            this.y = y;
            this.dx = dx;
            this.dy = dy;
            this.button = button;
            this.dwheel = dwheel;
            this.state = state;
            this.nanos = nanos;
        }

        public static FakeMouseEvent move(int dx, int dy) {
            return new FakeMouseEvent((int) FakeMouse.x, (int) FakeMouse.y, dx, dy, 0, 0, false, System.nanoTime());
        }
    }

    public static boolean next() {
        currentEvent = eventQueue.poll();
        System.out.println("FakeMouse.next is called, returning " + String.valueOf(currentEvent != null));
        return currentEvent != null;

    }

    public static int getX() {
        return (int) x;
    }

    public static int getY() {
        return (int) y;
    }

    public static int getDX() {
        int retval = dx;
        dx = 0;
        return retval;
    }

    public static int getDY() {
        int retval = dy;
        dy = 0;
        return retval;
    }

    public static int getEventButton() {
        return currentEvent.button;
    }

    public static boolean getEventButtonState() {
        return currentEvent.state;
    }

    public static int getEventX() {
        return currentEvent.x;
    }

    public static int getEventY() {
        return currentEvent.y;
    }

    public static int getEventDX() {
        return currentEvent.dx;
    }

    public static int getEventDY() {
        return currentEvent.dy;
    }

    public static int getEventDWheel() {
        return currentEvent.dwheel;
    }

    public static long getEventNanoseconds() {
        return currentEvent.nanos;
    }

    public static void addEvent(FakeMouseEvent event) {
        if (event.state) {
            pressedButtons.add(event.button);
            accumPressedButtons.add(event.button);
        } else {
            pressedButtons.remove(event.button);
        }
        eventQueue.add(event);
    }

    public static void pressButton(int button) {
        if (!pressedButtons.contains(button)) {
            System.out.println("Button " + String.valueOf(button) + " is pressed");
            addEvent(new FakeMouseEvent(x, y, 0, 0, 0,  button, true, System.nanoTime()));
        }
    }

    public static void releaseButton(int button) {
        // TODO - match the press event and add dx, dy? Is that necessary?
        if (pressedButtons.contains(button)) {
            System.out.println("Button " + String.valueOf(button) + " is released");
            addEvent(new FakeMouseEvent(x, y, 0, 0, 0, button, false, System.nanoTime()));
        }
    }

    public static void addMovement(int dx, int dy) {
        FakeMouse.dx = dx;
        FakeMouse.dy = dy;
        x += dx;
        y += dy;
        accumDx += dx;
        accumDy += dy;
    }

    public static boolean isButtonDown(int button) {
        return pressedButtons.contains(button);
    }


    public static boolean isInsideWindow() {
        return true;
    }

    public static void setCursorPosition(int newX, int newY) {
        x = newX;
        y = newY;
    }

    public static void setGrabbed(boolean grabbed) {
        FakeMouse.grabbed = grabbed;
    }

    public static boolean isGrabbed() {
        return grabbed;
    }
}
