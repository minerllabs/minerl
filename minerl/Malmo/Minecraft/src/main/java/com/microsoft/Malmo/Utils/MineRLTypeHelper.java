package com.microsoft.Malmo.Utils;

import com.google.gson.JsonObject;
import net.minecraft.entity.player.InventoryPlayer;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.util.ResourceLocation;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

public class MineRLTypeHelper {


    /**
     * @return A String item type suitable for Types.xsd or passing back to MineRL in messages, or
     *     null if such a String could not be found.
     */
    @Nullable
    public static String getItemType(Item item) {
        ResourceLocation resourceLocation = Item.REGISTRY.getNameForObject(item);
        if (resourceLocation == null) {
            return null;
        } else {
            return resourceLocation.getResourcePath();
        }
    }

    @NotNull
    public static JsonObject jsonFromItemStack(ItemStack stack) {
        JsonObject jobj = new JsonObject();
        writeItemStackToJson(stack, jobj);
        return jobj;
    }

    public static void writeItemStackToJson(ItemStack stack, JsonObject jsonObject) {
        int metadata = stack.getMetadata();
        if (metadata < 0 || metadata > 15) {
            throw new RuntimeException(String.format("Unexpected metadata value %d.", metadata));
        }
        jsonObject.addProperty("type", MineRLTypeHelper.getItemType(stack.getItem()));
        jsonObject.addProperty("metadata", metadata);
        jsonObject.addProperty("quantity", stack.getCount());
    }

    /**
     * Find the lowest inventory index that matches the itemType and the metadata.
     * @param itemType The String name of the Item or ItemStack.
     * @param metadata The metadata or the damage of the ItemStack. Pass null to ignore this constraint.
     * @return The lowest inventory index matching the contraints, or null if no such slot is found.
     */
    @Nullable
    public static Integer inventoryIndexOf(InventoryPlayer inventory, String itemType, @Nullable Integer metadata) {
        Item parsedItem = Item.getByNameOrId(itemType);
        if (parsedItem == null || parsedItem.getRegistryName() == null)
            throw new IllegalArgumentException(itemType);
        ResourceLocation targetRegName = parsedItem.getRegistryName();

        for (int i = 0; i < inventory.getSizeInventory(); i++) {
            ItemStack stack = inventory.getStackInSlot(i);
            ResourceLocation regName = stack.getItem().getRegistryName();
            if (regName == null) {
                // 80% confident this will be AIR if the slot is empty, rather than null.
                throw new RuntimeException(String.format("null RegistryName at inventory index %d", i));
            }

            boolean flagItemTypeMatches = regName.equals(targetRegName);
            boolean flagItemMetadataMatches = (metadata == null) || (metadata == stack.getMetadata());

            if (flagItemTypeMatches && flagItemMetadataMatches) {
                return i;
            }
        }
        return null;
    }
}
