#import pdb
import player, deck, hands
from random import shuffle, randrange
from copy import deepcopy


class Table():
    def __init__(self, num_players, num_chips, big_blind):
        self.num_players = num_players
        self.num_chips = num_chips
        self.big_blind = big_blind
        
        self.deck = deck.Deck()
        self.com_cards = []
        self.pot = 0
        
        self.pd = \
        {'player'+str(i+1) : player.Player(stack=num_chips) for i in range(num_players)}
        
        self.seat_order = [player for player in self.pd.keys()]
        
        # SET BOT PROFILES
        for p in self.seat_order:
            if p != 'player1':
                self.pd[p].human = 0
                choice = 2
                if choice == 0:
                    self.pd[p] = bot_profiles.Calling_Station(stack = num_chips)
                    self.pd[p].bot_profile = 'calling_station'
                elif choice == 1:
                    self.pd[p] = bot_profiles.Tight_Aggressive(stack = num_chips)
                    self.pd[p].bot_profile = 'tight_aggressive'
                elif choice == 2:
                    from expert_bot_profile import Expert_Bot
                    self.pd[p] = Expert_Bot(stack = num_chips)
                    self.pd[p].bot_profile = 'expert'
                elif choice == 3:
                    self.pd[p] = bot_profiles.Loose_Aggressive(stack = num_chips)
                    self.pd[p].bot_profile = 'loose_aggressive'
                print(self.pd[p].bot_profile)
            else:
                self.pd[p].human = 1
        
        shuffle(self.seat_order)
        
        self.round = 1
        self.min_bet = big_blind
        self.left_to_act = []
        self.in_hand = []
        self.cost_to_play = 0
        
        self.deal_hole_cards()
        self.post_blinds()
        
    def deal_hole_cards(self):
        for p in self.seat_order:
            self.pd[p].draw_card(self.deck.draw_card())
        for p in self.seat_order:
            self.pd[p].draw_card(self.deck.draw_card())
    
    # ?maybe account for division of odd numbers / split chips?
    def post_blinds(self):
        
        self.in_hand = self.seat_order[:]
        for p in self.in_hand:
            self.pd[p].begin_hand_chips = self.pd[p].stack
        if len(self.seat_order) == 2:
            # helper function, blind order is different for 2players
            self.post_blinds_2player()
        else:
            # dealer+1 enough chips for SB
            if self.pd[self.seat_order[1]].stack >= self.big_blind//2:
                self.pd[self.seat_order[1]].contribute_chips(self.big_blind//2)
                self.pot += self.big_blind//2
            else: # dealer+1 not enough chips for SB
                self.pot += self.pd[self.seat_order[1]].stack
                self.pd[self.seat_order[1]].contribute_chips(\
                    self.pd[self.seat_order[1]].stack)
            # dealer+2 enough chips for BB
            if self.pd[self.seat_order[2]].stack >= self.big_blind:
                self.pd[self.seat_order[2]].contribute_chips(self.big_blind)
                self.pot += self.big_blind
            else: # dealer+2 not enough chips for BB
                self.pot += self.pd[self.seat_order[2]].stack
                self.pd[self.seat_order[2]].contribute_chips(\
                    self.pd[self.seat_order[2]].stack)
            # Set order of action, players in hand, cost_to_play
            if len(self.seat_order) == 3:
                self.left_to_act = self.seat_order[:]
            else:
                self.left_to_act = self.seat_order[3:] + self.seat_order[:3]
            self.in_hand = self.seat_order[:]
            self.cost_to_play = self.big_blind
        
    # post_blinds for only 2 players, helper func called by post_blinds()
    def post_blinds_2player(self):
        
        self.in_hand = self.seat_order[:]
        # dealer enough for SB
        if self.pd[self.seat_order[0]].stack >= self.big_blind//2:
            self.pd[self.seat_order[0]].contribute_chips(self.big_blind//2)
            self.pot += self.big_blind//2
        else: # dealer not enough for SB
            self.pot += self.pd[self.seat_order[0]].stack
            self.pd[self.seat_order[0]].contribute_chips( \
                self.pd[self.seat_order[0]].stack)
        # dealer+1 enough for BB
        if self.pd[self.seat_order[1]].stack >= self.big_blind:
            self.pd[self.seat_order[1]].contribute_chips(self.big_blind)
            self.pot += self.big_blind
        else: # dealer+1 not enough for BB
            self.pot += self.pd[self.seat_order[1]].stack
            self.pd[self.seat_order[1]].contribute_chips( \
                self.pd[self.seat_order[1]].stack)
        # Set order of action, players in hand, cost_to_play
        self.left_to_act = self.seat_order[:]
        self.cost_to_play = self.big_blind
        
    # if one player has contributed more chips than all the rest, return those chips
    # modify stack and pd
    def return_excess_chips(self):
        pd = deepcopy(self.pd)
        ih = self.in_hand[:]
        bs = [p for p in ih if pd[p].chips_in_pot == max([pd[k].chips_in_pot for k in ih])]
        print(bs)
        if len(bs) == 1:
            ihcpy = ih[:]
            plyr = bs[0]
            ihcpy.remove(plyr)
            nbscth = max([pd[p].chips_in_pot for p in ihcpy])
            if pd[plyr].chips_in_pot > nbscth: # if plyr who contr most contr more than next most
                amount = pd[plyr].chips_in_pot - nbscth
                self.pot -= amount
                self.pd[plyr].stack += amount
                self.pd[plyr].chips_in_pot -= amount
        
    # Creates input for showdown() from table state at end of hand
    # RETURN VALUE --> [(1stsidepot,[listofplyrselig,...]),...(mainpot,[listofeligplyrs])]
    def create_pots(self):
        pd = deepcopy(self.pd)
        ih = self.in_hand[:]
        all_in = [p for p in ih if pd[p].stack == 0]
        if len(all_in) == 0:
            return [(self.pot, self.in_hand[:])]
        small_stacks = sorted(set([self.pd[p].begin_hand_chips for p in all_in]))
        print('pre-subtract small stacks ' + str(small_stacks))
        print('post-subtract small stacks ' + str(small_stacks))
        pots_plyrs = []
        all_plyrs = self.seat_order[:]
        ih_plyrs = ih[:]
        for i, n in enumerate(small_stacks):
            pot = 0
            plyrs = ih_plyrs[:]
            for p in all_plyrs:
                amount = min(n, pd[p].chips_in_pot)
                pot += amount
                self.pot -= amount
            pots_plyrs.append((pot, plyrs))
            for p in ih_plyrs[:]:
                if pd[p].begin_hand_chips == small_stacks[i] and pd[p].stack == 0:
                    ih_plyrs.remove(p)
        # subtract from each sidepot, the total of all previous sidepots
        pots = [x[0] for x in pots_plyrs]
        newpots = []
        for i,pot in enumerate(pots):
            newpots.append(pot - sum(newpots[:i]))
        print('pots ' + str(pots))
        newtups = []
        for i,pot_plyr in enumerate(pots_plyrs):
            newtups.append((newpots[i],pot_plyr[1]))
        print('return pots_plyrs ', newtups)
        return newtups

    def clean_table_after_hand(self):
        self.pot = 0
        self.com_cards = []
        self.min_bet = self.big_blind
        self.round = 1
        self.left_to_act = []
        self.in_hand = []
        self.cost_to_play = 0
        for plyr in self.seat_order:
            self.pd[plyr].clean_player_after_hand()

    def repop_left_to_act(self, plyr_str):
        self.left_to_act = []
        players = self.seat_order[self.seat_order.index(plyr_str)+1:] + self.seat_order[:self.seat_order.index(plyr_str)]
        for plyr in players:
            if plyr in self.in_hand:
                self.left_to_act.append(plyr)

    def bet(self, plyr, amount):
        if self.pd[plyr].stack >= self.min_bet:
            assert(amount >= self.min_bet)
        assert(amount <= self.pd[plyr].stack)
        self.pot += amount
        self.pd[plyr].contribute_chips(amount)
        self.cost_to_play += amount
        self.min_bet = amount
        self.repop_left_to_act(plyr)
        
    def check(self, plyr):
        if plyr in self.left_to_act:
            self.left_to_act.remove(plyr)
    
    def all_in(self, plyr, amount):
        assert(self.pd[plyr].stack == amount)
        self.pot += amount
        self.pd[plyr].contribute_chips(amount)
        self.cost_to_play += amount
        self.left_to_act.remove(plyr)
        # if amount is less than legal raise, do not reopen betting except to call !!
        # working here bug here, as is might be fine...
        if amount > self.min_bet:
            self.min_bet = amount
        self.repop_left_to_act(plyr)
    
    def call(self, plyr, amount):
        assert(amount <= self.pd[plyr].stack)
        self.pot += amount
        self.pd[plyr].contribute_chips(amount)
        self.left_to_act.remove(plyr)

    def _raise(self, plyr, raise_amount):
        assert(raise_amount >= min(self.pd[plyr].stack, self.min_bet))
        true_cost = self.cost_to_play-self.pd[plyr].chips_this_round
        assert(raise_amount + true_cost <= self.pd[plyr].stack)
        self.pot += raise_amount+true_cost
        self.pd[plyr].contribute_chips(raise_amount+true_cost)
        self.cost_to_play += raise_amount
        self.min_bet = raise_amount
        self.repop_left_to_act(plyr)
    
    def fold(self, plyr):
        if plyr in self.left_to_act:
            self.left_to_act.remove(plyr)
        if plyr in self.in_hand:
            self.in_hand.remove(plyr)

    def is_bb_option_avail(self, player):
        if self.round == 1 and self.cost_to_play == self.big_blind:
            if len(self.seat_order)==2:# only 2 players
                if player == self.seat_order[1]:
                    return True
            else:# more than 2 players
                if player == self.seat_order[2]:
                    return True
        return False
                
    def is_round_or_hand_over(self):
        if len(self.in_hand) == 1: # only one player
            winner_info_dict = self.reward(self.pot, [self.in_hand[0]])
            return ['hand over', winner_info_dict]
        elif self.left_to_act == []: # no players left to act
            if self.round == 4: # last round
                self.return_excess_chips()
                pots_plyrs_tup = self.create_pots()
                winner_info_dict = self.showdown(pots_plyrs_tup)
                return ['hand over', winner_info_dict]
            else:
                assert(self.round in [1,2,3])
                self.advance_round()
    
    # Returns legal actions of next player left to act with bounds on legal chip amounts
    def get_actions(self):
        p = self.left_to_act[0]
        if self.pd[p].stack == 0:
            return ('all-in',('check'))
        # Special BB options, what about less than legal raise amounts
        elif self.is_bb_option_avail(p) == True:
            return ('bb_options',('raise',min(self.pd[p].stack,self.min_bet),self.pd[p].stack),\
            ('check'),('fold'), p)
        # Check Bet Fold, table is open
        elif self.pd[p].chips_this_round == self.cost_to_play: # if table is open, bet/check/fold
            return ('check_options',('bet',min(self.pd[p].stack,self.min_bet),self.pd[p].stack),\
            ('check'), ('fold'), p)
        # Table is bet, p.stack is enough for call, not enough for legal raise
        elif (self.pd[p].chips_this_round < self.cost_to_play) and (self.pd[p].stack >= self.cost_to_play - self.pd[p].chips_this_round) and (self.pd[p].stack < self.cost_to_play - self.pd[p].chips_this_round + self.min_bet):
            return ('call_all_in_options', ('call',min(self.pd[p].stack,self.cost_to_play-self.pd[p].chips_this_round)),\
            ('all-in',self.pd[p].stack),\
            ('fold'), p)
        # Call Raise Fold, table is bet
        else:
            return ('call_options',('call',min(self.pd[p].stack,self.cost_to_play-self.pd[p].chips_this_round)),\
            ('raise',min(self.pd[p].stack,self.min_bet),self.pd[p].stack-self.cost_to_play+self.pd[p].chips_this_round),\
             ('fold'), p)
        
    def apply_action(self, plyr, action, amount=0):
        if action == 'raise':
            self._raise(plyr, amount)
        elif action == 'check':
            self.check(plyr)
        elif action == 'fold':
            self.fold(plyr)
        elif action == 'bet':
            self.bet(plyr, amount)
        elif action == 'call':
            self.call(plyr, amount)
        elif action == 'all_in':
            self.all_in(plyr, amount)
        maybe_winner_info = self.is_round_or_hand_over()
        if maybe_winner_info:
            return maybe_winner_info

    def advance_round(self):
        if self.round == 1:# preflop to flop, deal 3 com_cards
            self.com_cards.append(self.deck.draw_card())
            self.com_cards.append(self.deck.draw_card())
            self.com_cards.append(self.deck.draw_card())
        elif self.round == 2:# flop to turn, deal 1 com_card
            self.com_cards.append(self.deck.draw_card())
        elif self.round == 3:# turn to river, deal 1 com_card
            self.com_cards.append(self.deck.draw_card())
        # advance round
        self.round += 1
        # reset cost_to_play, min_bet
        self.cost_to_play = 0
        self.min_bet = self.big_blind
        # reset players chips_this_round, BUT NOT chips_in_pot
        for plyr in self.seat_order[1:] + [self.seat_order[0]]:
            self.pd[plyr].chips_this_round = 0
            # Reset left_to_act
            if plyr in self.in_hand:
                self.left_to_act.append(plyr)

    def move_button_remove_chipless_players(self):
        new_seats = []
        for plyr in self.seat_order[1:] + [self.seat_order[0]]:
            if self.pd[plyr].stack > 0:
                new_seats.append(plyr)
            else:
                self.pd.pop(plyr)
        self.seat_order = new_seats[:]
        
    # called by showdown(), break ties among same hand_rank
    # input = [(player2,[14,12,11,9,3]),...]
    # output = ['player2',...]
    def break_ties(self, plyr_tb_tups):
        plyrs = [x[0] for x in plyr_tb_tups]
        tbs = [x[1] for x in plyr_tb_tups]
        while(True):
            if tbs[0] == []: # no more elements to tiebreak
                return plyrs
            mx = max([tbs[n][0] for n in range(len(tbs))])
            for i,p in enumerate(plyrs[:]):
                if tbs[i][0] < mx:
                    if p in plyrs:
                        plyrs.remove(p)
            if len(plyrs) == 1:
                return plyrs
            else:
                for i,tblst in enumerate(tbs):
                    tbs[i] = tblst[1:]
    
    def reward(self, pot, plyrs):
        winner_info = dict((plyr, 0) for plyr in plyrs)
        remainder = pot % len(plyrs)
        pot -= remainder
        for p in plyrs:
            winner_info[p] += (pot//len(plyrs))
            self.pd[p].stack += (pot//len(plyrs))
        while(remainder):
            for p in self.in_hand[1:]+[self.in_hand[0]]:
                if remainder > 0:
                    self.pd[p].stack += 1
                    winner_info[p] += 1
                    remainder -= 1
        return winner_info
    
    # Takes the 'pots_plyrs' output from create_pots()
    # Ends the hand, rewards players
    # Should prompt for next_hand with this
    def showdown(self, pots_plyrs_tup):
        print('pots_plyrs_tup inside showdown ', pots_plyrs_tup)
        main_dict = {}
        for p in self.in_hand:
            self.assign_hand_rank(p)
        for pot_plyr in pots_plyrs_tup:
            print('pot_plyr in pots_plyrs_tup showdown loop ' + str(pot_plyr))
            high = max([self.pd[p].hand_rank for p in pot_plyr[1]])
            pot = pot_plyr[0]
            highplyrs = [p for p in pot_plyr[1] if self.pd[p].hand_rank == high]
            print('pot and plyrs with highest hand rank from tuple ' + str(pot) + ' ' + str(highplyrs))
            tbs = [self.pd[p].tie_break[:] for p in highplyrs]
            plyrs_tbs_tups = [(highplyrs[i], tbs[i]) for i in range(len(highplyrs))]
            dict = self.reward(pot, self.break_ties(plyrs_tbs_tups))
            for k in dict.keys():
                if k not in main_dict.keys():
                    main_dict[k] = dict[k]
                else:
                    main_dict[k] += dict[k]
        print('showdown main_dict returned ' + str(main_dict))
        return main_dict
        
    # Assigns hand_rank and tie_break values to the Player object
    def assign_hand_rank(self, plyr):
        hand = self.pd[plyr].hand + self.com_cards
        handranks_w_ace_as_one = []
        for card in hand:
            if card[0] == 14:
                handranks_w_ace_as_one.append(1)
                handranks_w_ace_as_one.append(14)
            else:
                handranks_w_ace_as_one.append(card[0])
        handranks_w_ace_as_one.sort(reverse=True)
        if hands.straight_flush_finder(hand):
            self.pd[plyr].hand_rank = 9
            self.pd[plyr].tie_break = hands.straight_flush_finder(hand)
        elif hands.four_of_a_kind_finder(hand):
            self.pd[plyr].hand_rank = 8
            self.pd[plyr].tie_break = hands.four_of_a_kind_finder(hand)
        elif hands.fullhouse_finder(hand):
            self.pd[plyr].hand_rank = 7
            self.pd[plyr].tie_break = hands.fullhouse_finder(hand)
        elif hands.flush_finder(hand):
            self.pd[plyr].hand_rank = 6
            self.pd[plyr].tie_break = hands.flush_finder(hand)
        elif hands.straight_finder(handranks_w_ace_as_one):
            self.pd[plyr].hand_rank = 5
            self.pd[plyr].tie_break = hands.straight_finder(handranks_w_ace_as_one)
        elif hands.three_of_a_kind_finder(hand):
            self.pd[plyr].hand_rank = 4
            self.pd[plyr].tie_break = hands.three_of_a_kind_finder(hand)
        elif hands.two_pair_finder(hand):
            self.pd[plyr].hand_rank = 3
            self.pd[plyr].tie_break = hands.two_pair_finder(hand)
        elif hands.one_pair_finder(hand):
            self.pd[plyr].hand_rank = 2
            self.pd[plyr].tie_break = hands.one_pair_finder(hand)
        else:
            self.pd[plyr].hand_rank = 1
            self.pd[plyr].tie_break = hands.highcard_finder(hand)

# Called after showdown/reward, remove busted plyrs, reset tmp vars, 
    def next_hand(self):
        self.move_button_remove_chipless_players()
        self.clean_table_after_hand()
        self.post_blinds()
        self.deck = deck.Deck()
        self.deal_hole_cards()
        


# Make test suite to test for hand winner detection, tie break detection, ...
if __name__ == "__main__":
    t = Table(9, 400, 20)
    t.apply_action(t.left_to_act[0], 'call', 20)
    t.apply_action(t.left_to_act[0], 'call', 20)
    t.apply_action(t.left_to_act[0], 'call', 20)
    t.apply_action(t.left_to_act[0], 'call', 20)
    t.apply_action(t.left_to_act[0], 'call', 20)
    t.apply_action(t.left_to_act[0], 'call', 20)
    t.apply_action(t.left_to_act[0], 'call', 20)
    t.apply_action(t.left_to_act[0], 'call', 10)
    t.apply_action(t.left_to_act[0], 'check')
    t.com_cards = [(10,'S'), (11,'S'), (12,'S'), (3,'H'), (3,'D')]
    t.round = 4
    t.left_to_act = []
    # deck might have unreal values (five 3's for example)
    t.pd[t.seat_order[0]].hand = [(13,'S'), (14,'S')] # completes straight(royal)flush
    t.pd[t.seat_order[1]].hand = [(3,'S'), (3,'C')] # completes 4ofakind
    t.pd[t.seat_order[2]].hand = [(10,'H'), (10,'D')] # full house
    t.pd[t.seat_order[3]].hand = [(4,'S'), (2,'S')] # flush
    t.pd[t.seat_order[4]].hand = [(13,'D'), (14,'D')] # straight
    t.pd[t.seat_order[5]].hand = [(6,'D'), (3,'C')] # 3ofakind, tie_break has too many vals
    t.pd[t.seat_order[6]].hand = [(12,'H'), (14,'D')] # 2pair
    t.pd[t.seat_order[7]].hand = [(7,'D'), (14,'D')] # 1pair, tie_break has too many vals
    t.pd[t.seat_order[8]].hand = [(4,'D'), (9,'D')] # 1pair with lower tiebreak
    for i,p in enumerate(t.seat_order):
        t.assign_hand_rank(p)
        
##############################################
# TEST break_ties()
# input --> [('player1',[14,13,12,11,10]), ('player2',[14,13,12,11,10])]
    x = [('player1',[14,13,12,11,10]), ('player2',[14,13,12,11,10])]
    print(t.break_ties(x))
##############################################
# TEST SUITE for create_pots()
# need to assert that amounts after showdown() with create_pots() are the same amounts of chips
# add up all player's stacks before showdowns() and break_ties(), compare to amounts given to players with reward()
    # need to make series of plyrs with about half being all-in, 
    t.in_hand = t.seat_order[:]
    created_chips_total = 0
    for p in t.seat_order:
        val = randrange(10, 1001)
        val = val//10*10
        print('val is ' + str(val))
        t.pd[p].stack = val
        t.pd[p].begin_hand_chips = val
    for p in t.seat_order:
        choice = randrange(0,2)
        if choice:
            # player has gone all-in
            amt = t.pd[p].stack
            t.pot += amt
            t.pd[p].stack -= amt
            t.pd[p].chips_in_pot = amt
            created_chips_total += amt
        else:
            # player has contr some and folded
            val = randrange(10, t.pd[p].stack)
            val = val//10*10
            t.pot += val
            t.pd[p].stack -= val
            t.pd[p].chips_in_pot = val
            t.in_hand.remove(p)
            created_chips_total += val
    for p in t.seat_order:
        print(p)
        print('begin hand chips ' + str(t.pd[p].begin_hand_chips))
        print('chips in pot ' + str(t.pd[p].chips_in_pot))
        print('stack ' + str(t.pd[p].stack))
    before_return = t.pot
    t.return_excess_chips()
    print('returned this many chips ' + str(before_return - t.pot))
    created_chips_total -= (before_return - t.pot)
    pot_plyrs_tups = t.create_pots()
    sum_pots = sum([x[0] for x in pot_plyrs_tups])
    print('sum_pots ' + str(sum_pots) + ' ' + 'created_chips_total ' + str(created_chips_total))
    assert(created_chips_total == sum_pots)
    print('sum_pots ' + str(sum_pots) + ' ' + 'created_chips_total ' + str(created_chips_total))
    