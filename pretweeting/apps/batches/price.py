from pretweeting import consts

def get_price(count, batch):
    return compute_price(count.number, batch.total_messages)

def compute_price(num_mentions, total_messages):
    return (consts.ALL_TWITTER_PRICE 
            * float(num_mentions) 
            / total_messages)