package com.example;

import java.util.List;

public class Order {
    // FR-001 T001
    public void pay(int index, List items) {
        if (index <= items.size()) {
            try {
                items.get(index);
            } catch (Exception e) {}
        }
    }
}
