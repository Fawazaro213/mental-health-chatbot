import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import SGD

# Download necessary NLTK data (only needs to be done once)
# nltk.download('punkt')
# nltk.download('wordnet')

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# --- 1. Load and Preprocess Data ---
print("Loading and preprocessing data...")
words = []
classes = []
documents = []
ignore_letters = ['?', '!', '.', ',']
intents = json.loads(open('intents.json').read())

for intent in intents['intents']:
    for pattern in intent['patterns']:
        # Tokenize each word in the sentence
        word_list = nltk.word_tokenize(pattern)
        words.extend(word_list)
        # Add the document to our corpus
        documents.append((word_list, intent['tag']))
        # Add the tag to our classes list if not already present
        if intent['tag'] not in classes:
            classes.append(intent['tag'])

# Lemmatize words, convert to lower case, and remove duplicates
words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_letters]
words = sorted(list(set(words)))
classes = sorted(list(set(classes)))

# Save the words and classes lists to binary files for later use
pickle.dump(words, open('words.pkl', 'wb'))
pickle.dump(classes, open('classes.pkl', 'wb'))

# --- 2. Create Training Data ---
print("Creating training data...")
training = []
output_empty = [0] * len(classes)

for doc in documents:
    bag = []
    word_patterns = doc[0]
    # Lemmatize each word in the pattern
    word_patterns = [lemmatizer.lemmatize(word.lower()) for word in word_patterns]
    for word in words:
        # Create a bag of words: 1 if word is in the pattern, 0 otherwise
        bag.append(1) if word in word_patterns else bag.append(0)

    # Create the output row: 1 for the correct tag, 0 for others
    output_row = list(output_empty)
    output_row[classes.index(doc[1])] = 1
    training.append([bag, output_row])

# Shuffle the training data and convert to a NumPy array
np.random.shuffle(training)
training = np.array(training, dtype=object)

# Split the data into training features (X) and labels (Y)
train_x = list(training[:, 0])
train_y = list(training[:, 1])

# --- 3. Build and Train the Neural Network Model ---
print("Building and training the model...")
model = Sequential()
model.add(Dense(128, input_shape=(len(train_x[0]),), activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(len(train_y[0]), activation='softmax'))

# Compile the model with Stochastic Gradient Descent optimizer
sgd = SGD(learning_rate=0.01, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

# Train the model
model.fit(np.array(train_x), np.array(train_y), epochs=200, batch_size=5, verbose=1)

# --- 4. Save the Trained Model ---
model.save('chatbot_model.h5')
print("Done. Model saved as chatbot_model.h5")