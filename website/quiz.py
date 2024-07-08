import random
import torch
import fitz  # PyMuPDF
import spacy

# Load SpaCy model for sentence segmentation and named entity recognition
nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf_quiz(file_path):
    doc = fitz.open(file_path)
    text = ''
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text

def preprocess_text(text):
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    return sentences

def generate_quiz_from_summary(summary, num_mcq=5, num_tf=5):
    sentences = preprocess_text(summary)
    
    definition_terms = extract_definitions_and_terms(sentences)
    
    mcq_questions = generate_definition_questions(definition_terms, num_mcq)
    
    quiz = mcq_questions
    random.shuffle(quiz)
    
    return quiz

def extract_definitions_and_terms(sentences):
    definitions_and_terms = []
    for sentence in sentences:
        if ':' in sentence:
            term, definition = sentence.split(':', 1)
            term, definition = term.strip(), definition.strip()
            definitions_and_terms.append((term, definition))
        elif '-' in sentence:
            term, definition = sentence.split('-', 1)
            term, definition = term.strip(), definition.strip()
            definitions_and_terms.append((term, definition))
    return definitions_and_terms

def generate_definition_questions(definitions_and_terms, num_questions):
    num_questions = min(num_questions, len(definitions_and_terms))
    questions = []
    
    for term, definition in random.sample(definitions_and_terms, num_questions):
        question = f"What is '{term}'?"
        
        options = generate_plausible_options(definition, [d for _, d in definitions_and_terms])
        random.shuffle(options)
        
        if definition not in options:
            options[random.randint(0, min(len(options) - 1, 3))] = definition
        
        questions.append({
            'question': truncate_question(question, 10),
            'options': [truncate_choice(option, 1) for option in options],
            'correct_answer': definition
        })
    
    return questions

def generate_plausible_options(correct_definition, definitions):
    options = [correct_definition]
    random.shuffle(definitions)
    options += random.sample([definition for definition in definitions if definition != correct_definition], min(3, len(definitions) - 1))
    return options[:4]

def truncate_question(question, word_limit):
    words = question.split()
    return ' '.join(words[:word_limit])

def truncate_choice(choice, word_limit):
    words = choice.split()
    return ' '.join(words[:word_limit])

def generate_questions_from_summary(summary, num_questions=10):
    sentences = preprocess_text(summary)
    questions = []
    
    for sentence in sentences:
        inputs = tokenizer.encode_plus(sentence, add_special_tokens=True, return_tensors="pt")
        input_ids = inputs["input_ids"].tolist()[0]
        text_tokens = tokenizer.convert_ids_to_tokens(input_ids)
        
        outputs = model(**inputs)
        answer_start_scores = outputs.start_logits
        answer_end_scores = outputs.end_logits
        
        answer_start = torch.argmax(answer_start_scores)
        answer_end = torch.argmax(answer_end_scores) + 1
        
        answer = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(input_ids[answer_start:answer_end]))
        question = sentence.replace(answer, "______")
        
        questions.append({
            'question': truncate_question(question, 10),
            'answer': truncate_choice(answer, 1)
        })
    
    random.shuffle(questions)
    return questions[:num_questions]