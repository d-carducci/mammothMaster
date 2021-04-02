# mammothMaster
A Fallen London grind cycle analysis tool 

##### What is this? 
It's a python script to analyse the efficiency of different grinds in the Fallen London browser game; it was conceived to analyse different [mammoth ranching](https://docs.google.com/document/d/1BL0x9e4CwhYtIMuY5uk-iD0LKezy3RCUpse3auAbXKY/edit) routines but it should be easily repurposed for other grinds.

##### How does it work?
It takes your stats and the steps you intend to take, uses them to represent the grind as a matrix and lets numpy do some math to figure out whether it's viable or not and how efficient it is. 
It's rather unpolished and amateurish (because I'm an unpolished amateur programmer) but you should be able to implement new grinds and steps by defining new functions to initialize instances of the "recipe" custom class.
##### What do I need to run it?
Just the latest versions of python3, numpy, scipy, and matplotlib.

