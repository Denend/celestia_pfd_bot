**Celestia bot for submitting pay for data transactions**

**Insctructions**

1) Type /start to start the bot
2) Enter ip of the server with your light node
3) Enter password from the server

You ll see your node id, uptime score and number of pfd transactions

Now make sure you have enough test tokens on your wallet 
You can check this out with command 

curl -X GET http://localhost:26659/balance

If you wallet has enough tokens - you can easily submit the transaction with a button "Submit pay for blob tx"
If its successfull you will get a msg with your tx hash

After you are done with submitting pfd txs - dont forget to **close the session**

