import type { TriviaQuestion, WyrPrompt } from "./types";

export const TRIVIA_QUESTIONS: TriviaQuestion[] = [
  { prompt: "Which planet has the most moons?", choices: ["Earth", "Mars", "Saturn", "Venus"], answer: 2 },
  { prompt: "What is the only food that never spoils?", choices: ["Rice", "Honey", "Salt crackers", "Dried beans"], answer: 1 },
  { prompt: "Which animal's fingerprints are nearly identical to humans'?", choices: ["Koala", "Chimpanzee", "Raccoon", "Sloth"], answer: 0 },
  { prompt: "How many hearts does an octopus have?", choices: ["One", "Two", "Three", "Eight"], answer: 2 },
  { prompt: "Which country invented karaoke?", choices: ["South Korea", "Japan", "Philippines", "USA"], answer: 1 },
  { prompt: "What color is a polar bear's skin?", choices: ["White", "Pink", "Black", "Grey"], answer: 2 },
  { prompt: "Which of these is NOT a real jellyfish?", choices: ["Fried egg jellyfish", "Cannonball jellyfish", "Disco ball jellyfish", "Lion's mane jellyfish"], answer: 2 },
  { prompt: "Bananas are technically…", choices: ["Vegetables", "Berries", "Nuts", "Roots"], answer: 1 },
  { prompt: "Which instrument has 47 strings?", choices: ["Grand piano", "Concert harp", "Sitar", "Zither"], answer: 1 },
  { prompt: "What was the first toy advertised on TV?", choices: ["Barbie", "Mr. Potato Head", "Hula hoop", "Slinky"], answer: 1 },
  { prompt: "A group of flamingos is called a…", choices: ["Flamboyance", "Blush", "Parade", "Carnival"], answer: 0 },
  { prompt: "Which country eats the most chocolate per person?", choices: ["Belgium", "USA", "Switzerland", "France"], answer: 2 },
];

export const WYR_PROMPTS: WyrPrompt[] = [
  { a: "Always have to sing instead of speak", b: "Always have to dance everywhere you go" },
  { a: "Know every song lyric ever written", b: "Be able to instantly beat any video game" },
  { a: "Have a rewind button for your life", b: "Have a pause button for your life" },
  { a: "Only eat breakfast food forever", b: "Only eat dinner food forever" },
  { a: "Be famous but always slightly sweaty", b: "Be unknown but always perfectly comfortable" },
  { a: "Speak every human language", b: "Talk to animals" },
  { a: "Live in a treehouse mansion", b: "Live in an underwater dome" },
  { a: "Have hands for feet", b: "Have feet for hands" },
  { a: "Win an Olympic gold medal", b: "Win an Oscar" },
  { a: "Never wait in line again", b: "Never hit a red light again" },
];

export interface ImposterEntry {
  category: string;
  word: string;
}

export const IMPOSTER_ENTRIES: ImposterEntry[] = [
  { category: "Breakfast food", word: "Pancakes" },
  { category: "Breakfast food", word: "Croissant" },
  { category: "Ocean animal", word: "Octopus" },
  { category: "Ocean animal", word: "Sea turtle" },
  { category: "Party thing", word: "Piñata" },
  { category: "Party thing", word: "Karaoke machine" },
  { category: "Famous landmark", word: "Eiffel Tower" },
  { category: "Famous landmark", word: "Great Wall" },
  { category: "Movie genre", word: "Rom-com" },
  { category: "Movie genre", word: "Heist movie" },
  { category: "Kitchen item", word: "Air fryer" },
  { category: "Kitchen item", word: "Rolling pin" },
  { category: "Playground thing", word: "Seesaw" },
  { category: "Playground thing", word: "Monkey bars" },
  { category: "Winter thing", word: "Snowball fight" },
  { category: "Winter thing", word: "Hot chocolate" },
];

export function sample<T>(pool: T[], count: number): T[] {
  const copy = [...pool];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j]!, copy[i]!];
  }
  return copy.slice(0, count);
}
