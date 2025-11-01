---
id: 02-configure-initial-switch-settings
title: Configure Initial Switch Settings
description: Perform basic switch configuration tasks including securing access to the CLI, configuring passwords, and setting up MOTD banners.
difficulty: beginner
estimated_time: 45
topology_file: 02-configure-initial-switch-settings.yaml
diagram_file: 02_configure_initial_switch_settings.png
prerequisites:
  - 01-basic-device-configuration
---

# Lab 2: Configure Initial Switch Settings

## Lab Objectives

- Verify the default switch configuration
- Configure basic switch settings (hostname, passwords)
- Secure access to console and privileged EXEC mode
- Configure encrypted passwords
- Configure a message of the day (MOTD) banner
- Save configuration files to NVRAM
- Apply learned concepts to configure a second switch

## Lab Scenario

In this activity, you will perform basic switch configuration tasks. You will secure access to the command-line interface (CLI) and console ports using encrypted and plain text passwords. You will also learn how to configure messages for users logging into the switch. These message banners are also used to warn unauthorized users that access is prohibited.

**Note:** In Packet Tracer, the Catalyst 2960 switch uses IOS version 12.2 by default. If required, the IOS version can be updated from a file server in the Packet Tracer topology. The switch can then be configured to boot to IOS version 15.0, if that version is required.

## Prerequisites

- Completion of Lab 1 (Basic Device Configuration)
- Basic understanding of Cisco IOS navigation
- Familiarity with configuration modes

---

## Part 1: Verify the Default Switch Configuration

### Step 1: Enter privileged EXEC mode

You can access all switch commands from privileged EXEC mode. However, because many of the privileged commands configure operating parameters, privileged access should be password-protected to prevent unauthorized use.

The privileged EXEC command set includes the commands available in user EXEC mode, many additional commands, and the **configure** command through which access to the configuration modes is gained.

**Commands:**

```
Switch> enable
Switch#
```

**Explanation:**

- Notice that the prompt changed from `>` to `#` to reflect privileged EXEC mode
- In default configuration, no password is required

### Step 2: Examine the current switch configuration

Enter the show running-config command to view the current configuration.

**Commands:**

```
Switch# show running-config
```

**Questions to Consider:**

1. How many Fast Ethernet interfaces does the switch have?
2. How many Gigabit Ethernet interfaces does the switch have?
3. What is the range of values shown for the vty lines?
4. Which command will display the current contents of non-volatile random-access memory (NVRAM)?

**Check NVRAM:**

```
Switch# show startup-config
```

**Expected Output:**

```
startup-config is not present
```

**Explanation:**

- The switch responds with "startup-config is not present" because no configuration has been saved to NVRAM yet
- The running-config exists in RAM but hasn't been copied to NVRAM

---

## Part 2: Create a Basic Switch Configuration

### Step 1: Assign a name to the switch

To configure parameters on a switch, you may be required to move between various configuration modes. Notice how the prompt changes as you navigate through the switch.

**Commands:**

```
Switch# configure terminal
Switch(config)# hostname S1
S1(config)# exit
S1#
```

**Explanation:**

- `configure terminal` enters global configuration mode
- The `hostname` command changes the device name
- Notice how the prompt immediately reflects the new hostname

### Step 2: Secure access to the console line

To secure access to the console line, access config-line mode and set the console password to **letmein**.

**Commands:**

```
S1# configure terminal
S1(config)# line console 0
S1(config-line)# password letmein
S1(config-line)# login
S1(config-line)# exit
S1(config)# exit
S1#
```

**Explanation:**

- `line console 0` accesses the console line configuration mode
- `password letmein` sets the password for console access
- `login` enables password checking on the console line (without this, the password is not enforced)

**Question:** Why is the `login` command required?

### Step 3: Secure privileged mode access

Set the **enable** password to **c1$c0**. This password protects access to privileged mode.

**Note:** The `0` in `c1$c0` is a zero, not a capital O.

**Commands:**

```
S1> enable
S1# configure terminal
S1(config)# enable password c1$c0
S1(config)# exit
S1#
```

**Explanation:**

- The `enable password` command sets the password required to enter privileged EXEC mode
- This password is stored in plain text (we'll fix this in Step 4)

**Verify Configuration:**

```
S1# show running-config
```

**Observation:**

- Notice that both the console and enable passwords are displayed in **plain text**
- This could pose a security risk if someone is looking over your shoulder or obtains access to config files

### Step 4: Configure an encrypted password to secure access to privileged mode

The **enable password** should be replaced with the newer encrypted secret password using the **enable secret** command. Set the enable secret password to **itsasecret**.

**Commands:**

```
S1# configure terminal
S1(config)# enable secret itsasecret
S1(config)# exit
S1#
```

**Important Notes:**

- The `enable secret` password **overrides** the `enable password`
- If both are configured, you must enter the `enable secret` password to enter privileged EXEC mode
- The `enable secret` uses MD5 hashing for encryption

### Step 5: Verify that the enable secret password is added to the configuration file

Enter the show running-config command again to verify the new enable secret password is configured.

**Commands:**

```
S1# show running-config
```

You can abbreviate this command as:

```
S1# show run
```

**Questions:**

1. What is displayed for the enable secret password?
2. Why is the enable secret password displayed differently from what we configured?

**Expected in Configuration:**

```
enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
enable password c1$c0
```

**Explanation:**

- The number "5" indicates MD5 hashing
- The long string is the hashed version of "itsasecret"
- The enable password still appears in plain text

### Step 6: Encrypt the enable and console passwords

As you noticed in Step 5, the **enable secret** password was encrypted, but the **enable** and **console** passwords were still in plain text. We will now encrypt these plain text passwords using the **service password-encryption** command.

**Commands:**

```
S1# configure terminal
S1(config)# service password-encryption
S1(config)# exit
S1#
```

**Verify:**

```
S1# show running-config
```

**Expected Output:**

```
line con 0
 password 7 0822455D0A16
 login
!
enable password 7 0822404F1A0A
enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
```

**Explanation:**

- The number "7" indicates Cisco Type 7 encryption (weak, reversible)
- This provides basic protection against casual observation
- Type 7 can be easily decrypted, so it's not highly secure

**Question:** If you configure any more passwords on the switch, will they be displayed in the configuration file as plain text or in encrypted form? Explain.

---

## Part 3: Configure a MOTD Banner

### Step 1: Configure a message of the day (MOTD) banner

The Cisco IOS command set includes a feature that allows you to configure messages that anyone logging onto the switch sees. These messages are called message of the day, or MOTD banners. Enclose the banner text in quotations or use a delimiter different from any character appearing in the MOTD string.

**Commands:**

```
S1# configure terminal
S1(config)# banner motd "This is a secure system. Authorized Access Only!"
S1(config)# exit
S1#
```

**Alternative Delimiter Syntax:**

```
S1(config)# banner motd #
Enter TEXT message. End with the character '#'.
This is a secure system. Authorized Access Only!
#
```

**Explanation:**

- The MOTD banner is displayed before the login prompt
- Use delimiters (like `#` or `"`) to mark the beginning and end of the message
- Choose a delimiter that doesn't appear in your message text

**Questions:**

1. When will this banner be displayed?
2. Why should every switch have a MOTD banner?

**Answer:** The banner provides legal notice that the system is private property and unauthorized access is prohibited. This is important for legal protection.

---

## Part 4: Save and Verify Configuration Files to NVRAM

### Step 1: Verify that the configuration is accurate

Use the show run command to review your configuration.

**Commands:**

```
S1# show running-config
```

**Check for:**

- Correct hostname (S1)
- Console password configured and encrypted
- Enable password and enable secret configured
- MOTD banner configured
- Passwords encrypted (service password-encryption)

### Step 2: Save the configuration file

You have completed the basic configuration of the switch. Now back up the running configuration file to NVRAM to ensure that the changes made are not lost if the system is rebooted or loses power.

**Commands:**

```
S1# copy running-config startup-config
Destination filename [startup-config]? [Enter]
Building configuration...
[OK]
```

**Alternative Commands (all do the same thing):**

```
S1# copy run start
S1# write memory
S1# wr
```

**Explanation:**

- This copies the running-config (in RAM) to startup-config (in NVRAM)
- NVRAM is non-volatile memory, so configuration persists after reboot
- Always save your configuration before powering off!

**Question:** What is the shortest, abbreviated version of the `copy running-config startup-config` command?

**Answer:** `copy run start` or `wr`

### Step 3: Examine the startup configuration file

Verify that your changes were saved.

**Commands:**

```
S1# show startup-config
```

**Question:** Are all the changes that were entered recorded in the file?

---

## Part 5: Configure S2

You have completed the configuration on S1. You will now configure S2. If you cannot remember the commands, refer to Parts 1 to 4 for assistance.

### Configure S2 with the following parameters:

**Requirements:**

1. Device name: **S2**
2. Protect access to the console using the **letmein** password
3. Configure an enable password of **c1$c0** and an enable secret password of **itsasecret**
4. Configure an appropriate message to those logging into the switch
5. Encrypt all plain text passwords
6. Ensure that the configuration is correct
7. Save the configuration file to avoid loss if the switch is powered down

**Verification Steps:**

```
S2# show running-config
S2# show startup-config
```

**Test Access:**

1. Exit to test console password
2. Test enable password by entering privileged mode
3. Verify banner displays on login

---

## Key Concepts Summary

### Configuration Modes

- **User EXEC mode** (`Switch>`): Limited read-only access
- **Privileged EXEC mode** (`Switch#`): Full access to show commands
- **Global configuration mode** (`Switch(config)#`): Configure global settings
- **Line configuration mode** (`Switch(config-line)#`): Configure console/vty lines
- **Interface configuration mode** (`Switch(config-if)#`): Configure interfaces

### Password Types

- **Console password**: Secures console port access (line con 0)
- **Enable password**: Secures privileged EXEC mode (plain text, legacy)
- **Enable secret**: Secures privileged EXEC mode (MD5 hashed, preferred)
- **VTY password**: Secures Telnet/SSH access (line vty 0 15)

### Encryption Types

- **Type 5 (MD5)**: Used by enable secret, one-way hash, more secure
- **Type 7**: Used by service password-encryption, reversible, weak security
- **Type 9**: Scrypt hashing (newer IOS versions), very secure

### Important Commands Reference

**Enter/Exit Modes:**

```
enable                    # Enter privileged EXEC mode
configure terminal        # Enter global configuration mode
exit                      # Go back one mode level
end                       # Return to privileged EXEC mode from any config mode
```

**Configuration:**

```
hostname [name]                      # Set device hostname
line console 0                       # Enter console line config mode
password [password]                  # Set password
login                                # Enable password checking
enable password [password]           # Set enable password (plain text)
enable secret [password]             # Set enable secret (encrypted)
service password-encryption          # Encrypt all plain text passwords
banner motd [delimiter] [message]    # Set MOTD banner
```

**Verification:**

```
show running-config      # View current config (RAM)
show startup-config      # View saved config (NVRAM)
show version             # Show IOS version and hardware info
```

**Save Configuration:**

```
copy running-config startup-config   # Save config to NVRAM
write memory                         # Alternative save command
```

---

## Troubleshooting Tips

### Password Not Working

- **Issue:** Console password not being prompted
- **Solution:** Make sure you configured the `login` command under `line console 0`

### Enable Secret vs Enable Password

- **Issue:** Confusion about which password to use
- **Solution:** If both are configured, use the enable secret password (it overrides enable password)

### Configuration Lost After Reboot

- **Issue:** Configuration disappeared after restarting switch
- **Solution:** You forgot to save with `copy running-config startup-config`

### Banner Not Displaying

- **Issue:** MOTD banner doesn't appear
- **Solution:** Make sure delimiter is correctly placed and doesn't appear in the message text

---

## Practice Exercises

1. **Password Recovery:** Research how to perform password recovery on a Cisco switch
2. **Additional Security:** Configure VTY lines (Telnet/SSH) with passwords
3. **Banner Types:** Experiment with `banner login` and `banner exec` in addition to MOTD
4. **Configuration Management:** Practice using `show running-config` vs `show startup-config`
5. **Erase Configuration:** Learn how to erase startup config with `write erase` or `erase startup-config`

---

## Lab Completion Checklist

- [ ] S1 hostname configured
- [ ] S1 console password set to "letmein"
- [ ] S1 enable password set to "c1$c0"
- [ ] S1 enable secret set to "itsasecret"
- [ ] S1 passwords encrypted with service password-encryption
- [ ] S1 MOTD banner configured
- [ ] S1 configuration saved to NVRAM
- [ ] S2 fully configured with all parameters
- [ ] S2 configuration saved to NVRAM
- [ ] Verified console access requires password on both switches
- [ ] Verified privileged mode requires enable secret password
- [ ] Verified MOTD banner displays on login

---

## Summary

In this lab, you learned to:

- Navigate between different configuration modes on a Cisco switch
- Secure console access with passwords
- Configure both enable password and enable secret
- Understand the difference between Type 5 (MD5) and Type 7 encryption
- Use service password-encryption to encrypt plain text passwords
- Configure MOTD banners for security warnings
- Save configurations to NVRAM for persistence
- Apply learned concepts to configure multiple devices

These basic configuration skills form the foundation for all future network device management tasks!
