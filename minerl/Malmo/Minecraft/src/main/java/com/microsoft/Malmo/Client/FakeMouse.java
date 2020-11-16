package com.microsoft.Malmo.Client;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashSet;
import java.util.Set;

public class FakeMouse {
    private static int x;
    private static int y;
    private static int dx;
    private static int dy;

    private static Deque<FakeMouseEvent> eventQueue = new ArrayDeque<FakeMouseEvent>();
    private static FakeMouseEvent currentEvent;
    private static Set<Integer> pressedButtons = new HashSet<Integer>();

    public static class FakeMouseEvent {
        private int button;

        private boolean state;

        private int dx;
        private int dy;
        private int dwheel;

        private int x;
        private int y;
        private long nanos;

        private FakeMouseEvent(int x, int y, int dx, int dy, int button, boolean state, long nanos) {
            this.x = x;
            this.y = y;
            this.dx = dx;
            this.dy = dy;
            this.button = button;
            this.state = state;
            this.nanos = nanos;
        }

        public static FakeMouseEvent move(int dx, int dy) {
            return new FakeMouseEvent((int) FakeMouse.x, (int) FakeMouse.y, dx, dy, 0, false, System.nanoTime());
        }
    }

    public static boolean next() {
        currentEvent = eventQueue.poll();
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
        } else {
            pressedButtons.remove(event.button);
        }
        eventQueue.add(event);
    }

    public static void pressButton(int button) {
        if (!pressedButtons.contains(button)) {
            addEvent(new FakeMouseEvent(x, y, 0, 0, button, true, System.nanoTime()));
        }
    }

    public static void releaseButton(int button) {
        // TODO - match the press event and add dx, dy? Is that necessary?
        if (pressedButtons.contains(button)) {
            addEvent(new FakeMouseEvent(x, y, 0, 0, button, false, System.nanoTime()));
        }
    }

    public static void addMovement(int dx, int dy) {
        FakeMouse.dx = dx;
        FakeMouse.dy = dy;
        x += dx;
        y += dy;
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


}
