# order

## Requirements

### Requirement: Create order

The system creates an order when Order.java receives a request.

#### Scenario: Happy path

- **GIVEN** a shopper
- **WHEN** they submit an order
- **THEN** the order is stored

### Requirement: Ship notice

The system sends a ship notice from Outside.java after the order is stored.

#### Scenario: Notice sent

- **GIVEN** a stored order
- **WHEN** the order is ready
- **THEN** a ship notice is sent
