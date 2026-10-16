package com.example;

import java.util.List;

public class Order {
    public void pay(int index, List items) {
        if (index <= items.size()) {
            try {
                items.get(index);
            } catch (Exception e) {}
        }
    }
}
