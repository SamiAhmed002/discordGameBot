import os
import discord
import asyncio
import datetime
import random

from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

bot = commands.Bot(command_prefix="-") #sets the bot prefix

players = [] #list of players in the lobby
gameInProgress = False #whether or not a game is in progress
guessesAllowed = False #whether or not players are able to submit guesses - not same as gameInProgress
channels = [] #the 2 channels each player will receive their questions in
correct = [0, 0] #number of questions in the set gotten correct
randNum = [[], []] #randomly generated index of the questions assigned
set = [0, 0] #which set each player is on

#for players, channels, correct, randNum and set, 1st index is for Player 1 and 2nd index is for Player 2

@bot.event
async def on_connect():  #occurs once the program has logged into the bot
    print("Logged in") #output should be in the console, not on Discord

@bot.event
async def on_message(ctx): #accepts all answers without needing a command
  if guessesAllowed == True and (str(ctx.channel.name) == str(channels[0]) or str(ctx.channel.name) == str(channels[1])):
    if str(ctx.author) != "gameBot#7177": #bot will attempt to DM itself otherwise
      await guess(ctx, ctx.content)
  await bot.process_commands(ctx) #allows the other subroutines to be executed - removal of this line will stop all other subroutines from being executed

@bot.command(
  brief="Join the lobby",
  help="'-join' adds whoever uses it to the lobby. This command can only be used if there is no game in progress"
) #allows the user to call the subroutine by using its name in a command
async def join(ctx):  #subroutine for the join command - allows users to join the lobby before the game begins. Any data following the command will be ignored
  if gameInProgress == True: #blocks the command from being used if a game is in progress
    #users should never be allowed to alter the lobby while a game is in progress 
    await ctx.send("There is currently a game in progress, so this action cannot currently be performed.")
  else:
    response = ""
    flag = False
    for i in range(0, len(players)):  #compares sender of message to each player in the lobby to check if user is already in the lobby
      if ctx.author == players[i]:
        await ctx.channel.send("You are already in the lobby") #no user should be repeated in the list of players
        flag = True
    if flag == False:  #adds the user to the lobby if not already in and announces it
      players.append(ctx.author)
      response = (ctx.author.mention) + " has joined the lobby. \n"
      response = response + (str(len(players)) + " in lobby. \n")
      await ctx.send(response)

@bot.command(
  brief="Leave the lobby",
  help="'leave' removes whoever uses it from the lobby. This command can only be used if there is no game in progress"
)
async def leave(ctx): #subroutine to allow users to leave the lobby - users cannot remove each other with this command. Any data following the command will be ignored
  if gameInProgress == True: #blocks the command from being used if a game is in progress
    #users should never be allowed to alter the lobby while a game is in progress 
    await ctx.send("There is currently a game in progress, so this action cannot currently be performed.")
  else:
    response = ""
    flag = False
    index = 0
    for i in range(0, len(players)): #checks each player in the lobby to compare them to the user who wishes to leave
      if players[i] == ctx.author:
        flag = True #indicates that the user has been found and removed
        index = i #notes the index of the player to be removed
        #only remove player after the whole list has been checked to avoid indexing error
        response = str(ctx.author.mention) + " has left the lobby. \n"
        response = response + str(len(players) - 1) + " in lobby."
        
    if flag == False: #occurs if the user was not found in the lobby
      response = "You are not in the lobby."
    else:
      players.remove(players[index]) #removes the player who triggered the subroutine
    await ctx.send(response)


@bot.command(
  brief="See who is in the lobby",
  help="'-lobby' displays all lobby members (if any)."
)
async def lobby(ctx): #subroutine to display the lobby members. Any data following the command will be ignored
  #this command may be used while a game is in progress - lobby count & members are not modified
  response = ""
  if len(players) == 0: #informs the user if the lobby is empty
    await ctx.send("Lobby is empty")
  else:
    response = "Players in lobby (" + str(len(players)) + "): \n"
    for i in range(0, len(players)): #displays all the users in the lobby
      if i == 0: #specifies the first user as being the host
        response = response + (str(players[i].mention) + " (host) \n")
      else:
        response = response + str(players[i].mention + " \n")
    await ctx.send(response)


@bot.command(
  brief="Kick someone from the lobby",
  help="'-kick @user' removes the user mentioned from the lobby. This command can only be used by the host if there is no game in progress"
)
async def kick(ctx, *, user: discord.User):  #subroutine to allow the host to kick other players from the lobby
  #command must be followed by the mention of a user so that the 2nd argument passed is a Discord user. Program will return error otherwise
  if gameInProgress == True: #blocks the command from being used if a game is in progress
    #users should never be allowed to alter the lobby while a game is in progress 
    await ctx.send("There is currently a game in progress, so this action cannot currently be performed.")
  else:
    response = ""
    index = 0
    if len(players) == 0:  #occurs if there is no one in the lobby
      await ctx.send("There is no one in the lobby.")
    elif ctx.author != players[0]:  #ensures that no one other than the host is able to kick players
      await ctx.send("Only the host of the lobby may kick other players")
    else:
      flag = False
      for i in range(0, len(players)):
        if user.mention == players[i].mention:  #notes the index of the player to be kicked
          response = str(user.mention) + " has been kicked. \n"
          index = i
          #only remove player after the whole list has been checked to avoid indexing error
          response = response + str(len(players) - 1) + " in lobby."
          await ctx.send(response)
          flag = True
      if flag == False:  #if the host attempts to kick someone who is not in the lobby, they will be told this
        await ctx.send("This user is not in the lobby.")
      else:
        players.remove(players[index]) #removes the specified player from the lobby


@bot.command(
  brief="Start the game",
  help="'-start' prepares the game by creating a new channel for each player and then explaining the rules"
)
async def start(ctx): #subroutine to prepare the game. Any data following the command will be ignored
  global gameInProgress
  global channels
  #game must only start if: the host is the one who used the command, there are 2 players in the lobby, and there is no game already in progress
  if len(players) == 0 or ctx.author != players[0]: #prevents anyone who isn't the host from starting the game
    await ctx.send("Only the host may start the game.")
  elif len(players) != 2: #prevents the game starting without 2 players
    await ctx.send("There must be 2 players in the lobby in order to start the game. Current lobby count is " + str(len(players)))
  elif gameInProgress == True: #there must only be be 1 game in progress at a time. Start command must not create a new game if one already exists
    await ctx.send("There is already a game in progress.")
  else:
    await ctx.send("The game is starting!")
    guild = ctx.guild #fetches the server that the channels need to be created in and the roles need to be made in
    for i in range(0, 2):
      newRole = await guild.create_role(name="team-" + str(i + 1)) #creates the roles
      overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), ctx.me: discord.PermissionOverwrite(read_messages=True), newRole: discord.PermissionOverwrite(read_messages=True)} #sets the permissions for default users, the bot and the user with the new role in this order
      channels.append(await guild.create_text_channel("team-" + str(i + 1) + "-channel", overwrites=overwrites)) #creates a new private channel
      #private channel must only be viewable by users with admin privileges, the bot itself and the player the channel was created for
      await players[i].add_roles(newRole) #assigns the new role to the player
    gameInProgress = True #indicates that a game is in progress - must only be changed back to false once the game is over and the channels have been deleted
    await rules(ctx)

async def rules(ctx): #subroutine to send the rules to each channel and start the game
  #subroutine cannot be directly called by user
  #subroutine ends with reset of data changed in previous game and assignment of first question, so if this subroutine is amended always keep last section
  global channels
  global correct
  global guessesAllowed
  for i in range(0, 2): #sends a welcome message as well as the rules to each player
    await channels[i].send("Welcome Player " + str(i + 1)) 
    message = discord.Embed(title="Rules:", description="The aim of the game is to finish before the other player. You'll be presented with a series of maths questions and must answer the final question correctly to win. You'll have unlimited time but only 1 attempt to answer each question, and getting a question wrong will result in you getting another question. You may write things down, but do not use a calculator for any of the questions. Good luck!", color=0x336EFF)
    await channels[i].send(embed=message)
    message = discord.Embed(title="Formatting your answer", description="In the following situations when typing your answer, please format it like this:", color =0x336EFF) 
    message.add_field(name="All answers", value="Type '-g' and then your answer", inline=False)
    message.add_field(name="Powers", value="Use ^ and put the power in brackets if it's more than one integer/letter e.g. 2^(2x) or 2^x", inline=False)
    message.add_field(name="Fractions/decimals", value="Use decimals to 3 s.f., e.g. 0.143 instead of 1/7", inline=False)
    message.add_field(name="Coordinates", value="Put in brackets without spaces, e.g. (-1,1)", inline=False)
    message.add_field(name="Factorising", value="Put in brackets without spaces and the larger x first. If both are the same put the larger number after x first, e.g. (2x+1)(x+5) or (x+5)(x+1)", inline=False)
    message.add_field(name="Multiple answers", value="Write each answer separated by commas and with no spaces, e.g. -4,7,9", inline=False)
    message.add_field(name="Integration", value="Use +c at the end of every indefinite integral, e.g. 0.25e^(4x)+c", inline=False)
    await channels[i].send(embed=message) #sends an embed explaining how players should format their answers
    await channels[i].send("The game will start in 30 seconds.")
  lastMessage=datetime.datetime.now() #stores the time that the program reaches this instruction
  #ensure that time warnings always match delays, including 10 second warning
  while datetime.datetime.now() <= lastMessage+datetime.timedelta(seconds=20): #delays the execution of the rest of the program until 20 seconds have passed
    await asyncio.sleep(1)
  for i in range(0, 2):
    await channels[i].send("The game will start in 10 seconds.") #gives users a 10 second warning before starting the game
    #give players enough time to read the information but not too much time as they'll get bored of waiting every single time
  lastMessage=datetime.datetime.now() #stores the time that the program reaches this instruction
  while datetime.datetime.now() <= lastMessage+datetime.timedelta(seconds=10): #delays the execution of the rest of the program until 10 seconds have passed
    await asyncio.sleep(1)
  for i in range(0, 2):
    await channels[i].send("The game has started!")
    #resetting data must be kept - new game will resume from progress of previous game if not and will result in an error
    correct[i] = 0 #resets all progress for the game to start from the beginning
    set[i] = 0 
    randNum[i].clear()
    await assignQuestion(ctx, players[i]) #assigns a question to each player
  guessesAllowed = True

async def assignQuestion(ctx, user): #subroutine to assign questions to players
  #subroutine cannot be directly called by user
  global randNum 
  global correct 
  global set
  questions = [["What is 343^⅔?", "What is ∫5x+4 dx?", "What are the coordinates of the centre of a circle with the equation (x+5)²+(y-4)²=36?", "Factorise x²+12x+32", "State, in ascending order, the values of x where the curve x(x-4)(x+5) crosses the x-axis.", "f(x)=sinx-eˣ. Find f'(x).", "A straight line passes through the points (3,9) and (5,1). Find its gradient.", "A line has the equation y=x²+4x+8. Find the coordinates of its turning point."], ["sin(15°) can be written in the form (√A-√B)/C. What are the values of A, B and C?", "f(x)=ln(sin(5x+3)). What is f'(x) in its simpliest form?", "When θ is small, fully simplify (7+2cos(2θ))/(tan(2θ)+3)).", "A particle moves in a straight line. Its displacement from its starting point, *s* m, at time *t* seconds is *s = t⁴+3t³-2t²*. Find the acceleration of the particle in m/s² when t=5. Do not include units.", "Find the values of R and α when 7cosθ - 24sinθ is expressed in the form Rcos(θ+α), where R>0 and 0<α<90°.", "Find the value of x, to 3s.f, when 10ˣ=6ˣ⁺²", "A particle of mass 5kg rolls down a smooth slope that is inclined at 30° to the horizontal. A force of 20N acts on the particle at an angle of 60° to the plane, slowing it down. Find the acceleration of the particle in m/s². Do not include units.", "Fully simplify (1-sinx)(1+cosecx)."], ["What is ∫x√(4x-1)?", "f'(x)=x²e³ˣ. What is f(x)?", "A curve has the equation y=xeˣ. The coordinates of its non-stationary point of inflection is (A, B/(e^C)). Find the values of A, B and C", "Find the binomial expansion of 4/(2+3x) up to and including the x³ term.", "Given that (x^2+1)/(x(x-2)) ≡ P + Q/x + R/(x-2), find the values of the constants P,Q and R.", "At time, *t* seconds, the surface area of a cube is *A* cm² and the volume is *V* cm³. The surface area of the cube expands at a constant rate of 2cm²/s. If d*V*/d*t* = x*V*ʸ, find the values of x and y.", "Fully simplify (1+cosx)/(1-cosx)", "In the interval 0≤x≤2π, the equation *sec(x+0.25π)=2* has 2 solutions: x=Aπ/C or x=Bπ/C. Find the values of A,B and C."]]

  for i in range(0,2):
    repeat = False
    if user == players[i]: #chooses a new question for the player and sends it to the channel
      randNum[i].append(random.randint(0,7)) #assigns index for new question
      for j in range(0, len(randNum[i])-1):
        if randNum[i][len(randNum[i])-1] == randNum[i][j]: #flags index as a repeat if it matches a previous question
          #important so that users do not abuse RNG to answer the same question multiple times without answering different questions
          repeat = True
      while repeat == True:
        repeat = False
        randNum[i][len(randNum[i])-1] = random.randint(0,7) #assigns a new index for new question
        for j in range(0, len(randNum[i])-1): #ensures there is no repeat
          if randNum[i][len(randNum[i])-1] == randNum[i][j]:
            repeat = True
      await channels[i].send(questions[set[i]][randNum[i][len(randNum[i])-1]])

async def guess(ctx, guess): #subroutine to check player's guess
  #subroutine cannot be directly called by user
  global correct
  global set
  global randNum
  global channels
  answers = [["49", "2.5x^2+4x+c", "(-5,4)", "(x+8)(x+4)", "-5,0,4", "cosx-e^x", "-4", "(-2,4)"], ["6,2,4", "5cot(5x+3)", "3", "386", "25,73.7", "7.02", "2.9", "cosxcotx"], ["0.025(4x-1)^2.5+0.0417(4x-1)^1.5+c", "0.333x^2e^(3x)-0.222xe^(3x)+0.0741e^(3x)+c", "-2,-2,2", "2-3x+4.5x^2-6.75x^3", "1,-0.5,2.5", "0.5,0.333", "(cosecx+cotx)^2", "1,17,12"]] #order of answers correspond to order of questions
  if str(ctx.channel.name) != str(channels[0]) and str(ctx.channel.name) != str(channels[1]): #prevents guesses being sent in other channels
    await ctx.send("Guesses may only be sent to 'team-1-channel' or 'team-2-channel' while a game is in progress.")
  elif ctx.author != players[0] and ctx.author != players[1]: #prevents anyone who isn't playing from sending guesses in the 2 channels
    await ctx.author.send("You are not a part of this game. Please do not interrupt.") #sends user a direct message
    #keep message as a DM instead of in game channel so it doesn't distract players
    await ctx.delete() #deletes the message sent to channel
  else:
    for i in range(0, 2):
      if ctx.author == players[i]:
          if guess == answers[set[i]][randNum[i][len(randNum[i])-1]]: #compares the guess to the correct answer
            await ctx.channel.send("Correct!")
            correct[i] = correct[i] + 1 #notes that the user has gotten another question correct
            if correct[i] == 2:
              set[i] = set[i] + 1 #moves player on to the next set of questions
              correct[i] = 0 #resets the correct counter
              randNum[i].clear() #clears the list of questions asked in the set
              #list must be cleared once all questions must be asked or else bot will be stuck in an infinite loop
          else: 
            await ctx.channel.send("Your answer was incorrect.")
            if len(randNum[i]) == len(answers[set[i]]):
              randNum[i].clear()
              #list must be cleared once all questions must be asked or else bot will be stuck in an infinite loop
          if set[i] == 3:
            await victory(ctx, ctx.author) #ends the game if set 3 has been completed
          else: 
            await assignQuestion(ctx, ctx.author) #assigns the player's next question
            #new question must be asked whether or not the previous question was asked correctly. Only exception is if the player has won
            
async def victory(ctx, winner): #subroutine to end the game
  #subroutine cannot be directly called by user
  #the winner must always be passed as an argument from assignQuestion subroutine
  global gameInProgress
  global guessesAllowed
  global channels
  global players
  global set
  global correct
  guessesAllowed = False #stops new guesses being registered
  for i in range(0,2): #informs each player that the game has ended and displays how many questions each player answered correctly
    await channels[i].send("The game has ended! " + str(winner) + " has won!")
    await channels[i].send(str(players[0]) + " answered " + str(set[0]*2+correct[0]) + " questions correctly, and " + str(players[1]) + " answered " + str(set[1]*2+correct[1]) + " questions correctly.") 
  lastMessage=datetime.datetime.now() #stores the time that the program reaches this instruction
  while datetime.datetime.now() <= lastMessage+datetime.timedelta(seconds=20): #delays the execution of the rest of the program until 20 seconds have passed so the messages can be read before channel deletion
    #give players enough time to read the information
    await asyncio.sleep(1)
  for channel in ctx.guild.channels: 
    if channel.name == "team-1-channel" or channel.name == "team-2-channel":
      await channel.delete() #deletes the channels used for the game
  for role in ctx.guild.roles:
    if role.name == "team-1" or role.name == "team-2":
      await role.delete() #deletes the roles used for the game
  channels.clear() #clears the channel list for future use
  gameInProgress = False #allows users to once again join and leave the lobby and start a game
  
my_secret = os.environ['TOKEN'] #TOKEN is stored in 'secrets'
bot.run(my_secret)
