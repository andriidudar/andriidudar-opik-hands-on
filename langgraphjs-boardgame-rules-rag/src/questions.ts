export interface Question {
  question: string;
  reference: string;
}

export const QUESTIONS: Question[] = [
  { question: "How many actions do I get on my turn in Tidewrack?", reference: "3 actions." },
  { question: "What happens to my skiff when it collects 3 leak tokens?", reference: "It sinks; salvage is discarded and the owner restarts from the harbor." },
  { question: "Can a Moth stand on the same tile as another Moth at the end of its move?", reference: "No." },
  { question: "How big does the Keeper's beam get once all shade cards are gone?", reference: "7 tiles." },
  { question: "How many quills can I hold in Quillfall?", reference: "At most 2." },
  { question: "In Quillfall, what is a molt and when does it happen?", reference: "Reshuffling the discard row (except the top card) into a new roost deck when the roost deck runs out." },
  { question: "Who wins Quillfall once someone reaches 15 points?", reference: "The player with the fewest points wins; the one reaching 15 loses." },
  { question: "Can I trade salvage with a player who is on a different reef tile in Tidewrack?", reference: "No, trading needs both players on the same tile." },
  { question: "What is the maximum number of players for Moth Lantern with the expansion pack?", reference: "The rulebooks don't say." },
  { question: "Does Tidewrack have a rule for playing with a timer?", reference: "The rulebooks don't say." },
];
