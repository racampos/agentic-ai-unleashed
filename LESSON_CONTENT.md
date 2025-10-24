# Basic Device Configuration

## Topology

```yaml
devices:
  - type: router
    name: Floor14
    hardware: cisco_2911
    device_id: c44b6160-930d-419b-805a-111111111114
    config: |
      hostname Floor14
    debug: true

  - type: switch
    name: Room-145
    hardware: cisco_2960
    device_id: c44b6160-930d-419b-805a-999999999145
    config: |
      hostname Room-145
    debug: true

  - type: switch
    name: Room-146
    hardware: cisco_2960
    device_id: c44b6160-930d-419b-805a-999999999146
    config: |
      hostname Room-146
    debug: true

  - type: host
    name: Manager-A
    hardware: host
    device_id: c44b6160-930d-419b-805a-000000000050
    config: |
      hostname Manager-A
    debug: true

  - type: host
    name: Reception-A
    hardware: host
    device_id: c44b6160-930d-419b-805a-000000000060
    config: |
      hostname Reception-A
    debug: true

  - type: host
    name: Manager-B
    hardware: host
    device_id: c44b6160-930d-419b-805a-000000000150
    config: |
      hostname Manager-B
    debug: true

  - type: host
    name: Reception-B
    hardware: host
    device_id: c44b6160-930d-419b-805a-000000000160
    config: |
      hostname Reception-B
    debug: true

connections:
  - interfaces:
      - device: Floor14
        interface: GigabitEthernet0/0
      - device: Room-145
        interface: FastEthernet0/24

  - interfaces:
      - device: Floor14
        interface: GigabitEthernet0/1
      - device: Room-146
        interface: FastEthernet0/24

  - interfaces:
      - device: Manager-A
        interface: FastEthernet0/0
      - device: Room-145
        interface: FastEthernet0/1

  - interfaces:
      - device: Reception-A
        interface: FastEthernet0/0
      - device: Room-145
        interface: FastEthernet0/2

  - interfaces:
      - device: Manager-B
        interface: FastEthernet0/0
      - device: Room-146
        interface: FastEthernet0/1

  - interfaces:
      - device: Reception-B
        interface: FastEthernet0/0
      - device: Room-146
        interface: FastEthernet0/2
```

## Addressing Table

| Device      | Interface | IP Address        | Default Gateway |
| ----------- | --------- | ----------------- | --------------- |
| Floor14     | G0/0      | 128.107.20.1/24   | N/A             |
|             |           | 2001:DB8:A::1/64  |                 |
|             | G0/1      | 128.107.30.1/24   | N/A             |
|             |           | 2001:DB8:B::1/64  |                 |
| Room-145    | VLAN 1    | No IP Address     |                 |
| Room-146    | VLAN 1    | No IP Address     |                 |
| Manager-A   | NIC       | 128.107.20.25/24  | 128.107.20.1    |
|             |           | 2001:DB8:A::25/64 | 2001:DB8:A::1   |
| Reception-A | NIC       | 128.107.20.30/24  | 128.107.20.1    |
|             |           | 2001:DB8:A::30/64 | 2001:DB8:A::1   |
| Manager-B   | NIC       | 128.107.30.25/24  | 128.107.30.1    |
|             |           | 2001:DB8:B::25/64 | 2001:DB8:B::1   |
| Reception-B | NIC       | 128.107.30.30/24  | 128.107.30.1    |
|             |           | 2001:DB8:B::30/64 | 2001:DB8:B::1   |

---

## Objectives

- Perform basic device configurations on a router and a switch.
- Verify connectivity and troubleshoot any issues.

---

## Scenario

Your network manager is impressed with your performance in your job as a LAN technician. She would like you to demonstrate your ability to configure a router that connects two LANs. Your tasks include configuring basic settings on a router and a switch using the Cisco IOS. You will also configure IPv6 addresses on network devices and hosts. You will then verify the configurations by testing end-to-end connectivity. Your goal is to establish connectivity between all devices.

**Note:** The switches do not have IP Addresses.

In this activity, you will configure the **Floor14** router, **Room-145** and **Room-146** switches, and the **PC hosts**.

To configure hosts, use the following CLI syntax:

```
Reception-A#ip address <ipv4 address> <subnet mask>
Reception-A#ipv6 address <ipv6 address>/64
Reception-A#ip default-gateway <ipv4 address>
Reception-A#ipv6 default-gateway <ipv6 address>
```

Use the router's global address as the host's IPv6 default gateway. Link local addresses are not supported.

---

## Requirements

For all devices:

- Use `cisco` as the user EXEC password for all lines.
- Use `class` as the encrypted privileged EXEC password.
- Encrypt all plaintext passwords.
- Configure an appropriate banner.
- The hosts are partially configured. Complete the IPv4 addressing, and fully configure the IPv6 addresses according to the Addressing Table.
- Document interfaces with descriptions.
- Save your configurations.
- Verify connectivity between all devices. All devices should be able to ping all other devices with IPv4 and IPv6.
- Troubleshoot and document any issues.
- Implement the solutions necessary to enable and verify full end-to-end connectivity.
