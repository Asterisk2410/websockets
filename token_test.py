from googletrans.gtoken import TokenAcquirer
acquirer = TokenAcquirer()
text = 'test'
tk = acquirer.do(text)
tk
