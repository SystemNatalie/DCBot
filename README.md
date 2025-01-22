# DCBot
A bot that manages different functionality for 2 discord servers, referred to as ServerA and ServerB.

[General Functionality]:
    
    * Allow users to send anonymous messages/replies using /secret or /secretreply
    
    * Snitch switch, which prints who says what for the afore mentioned functionality
    
    * Allows users without elevated permissions to pin messages by reacting to a message with a pin emoji
    
    * Delete all messages from a channel using /manualPurge

[ServerA Functionality]:
    
    * Periodically wipe a "whiteboard" channel at a set time daily.
    
    * Extended anonymous functionality as described in [General Functionality], with the addition of the option to DM the bot
      to send a message, which allows media to be sent as well.

      * Implements a feature called "YipYap" that lets people anonymously talk as 700+ different characters 
[ServerB Functionality]:
    
    * Act as a mute switch for two users/bots via /timeoutmomdad, which turns their mute switch on/off

Possible future functionality:
    
    * Ability to go back and retrieve messages from DMs?
    
    * Enumerate+print guild perms, to troubleshoot why functionality in one server might work and the other not?
   
    * Combination of repudiation tracker for a 3rd server, serverC (would need to remove anonymous functionality for serverC)
