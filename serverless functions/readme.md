# Cloud FaaS report

In this assignment, I have designed a front end in React JS that is served by a serverless backend. The serverless backend uses Fire store for data storage. 
Url: http://34.67.243.162/
What all i have implemented:
FaaS implementation
Bonus: Graphical output	
Bonus: Caching	
Bonus: Web-hosting

## FaaS implementation
### Design
![image](https://user-images.githubusercontent.com/25266353/100959237-dcb8f580-34eb-11eb-97df-f6582c30153b.png)
VM instance:
![image](https://user-images.githubusercontent.com/25266353/100961502-87cbae00-34f0-11eb-9e63-5f59bd971324.png)
Gcloud functions:
![image](https://user-images.githubusercontent.com/25266353/100961564-a16cf580-34f0-11eb-9a17-c76849a1bc12.png)

The functionality to check for cached data graphs and creating new graphs was seperated into two seperate functions to maintain modularity.
### The flow
 - The UI is written in React JS. When a user submits a URL and a book name, the UI drives the flow. It first asks the cache retreival function if the url has been submitted before.
 - The cached retreiver function accesses firestore DB and checks for a particular id. If the id was submitted before, the function returns a key value for numbero of words as keys and number of sentences as values.
 - If the cache does not find the id in Firestore, it returns false. The UI then submits the URL to sentence length function.
 - The function downloads the text at the url and This uses a regex parser to divide the text into lines and regex again to divide into words. Then number of words are counted in a sentence and a key value map is updated with key as the number of words and value of this key added by one. 
 - Once the whole text it tokenized, the results for this are stored in Firestore with the book id.
 - Once the values are sent to the front end, they are shown in the graph.
## Components
### UI 
![image](https://user-images.githubusercontent.com/25266353/100961892-4556a100-34f1-11eb-926c-b201215d3d4c.png)
User can paste a url and have their own label with book name or select one from auto complete drop down that appears on click of url text input. Reset clears all the grpahs, you can toggle individual graphs by clicking on labels in the key above the map.
The UI hits the follwing trigger with an http post request to check for precached results. Inside the POST body, a url is passed from where the resource is to be downloaded.
        `https://us-central1-rishabh-gajra.cloudfunctions.net/cached_data`
If this returns false, the following url is hit with same post body
        `https://us-central1-rishabh-gajra.cloudfunctions.net/sentence_length`
Code snippet:
``` javascript
    axios
      .post(
        `https://us-central1-rishabh-gajra.cloudfunctions.net/cached_data`,
        {
          url: u,
        }
      )
      .then((res) => {
        // console.log(res.data);
        if (res.data.success == true) {
          console.log(res.data);
          updateDataSet(l, Object.values(res.data.frequency));
          setLoading(false);
        } else {
          axios
            .post(
              `https://us-central1-rishabh-gajra.cloudfunctions.net/sentence_length`,
              {
                url: u,
              }
            )
            .then((res) => {
              // console.log(res.data.frequency);
              updateDataSet(l, Object.values(res.data.frequency));
              setLoading(false);
            })
            .catch(function (error) {
              console.log(error);
            });
        }
      })
      .catch(function (error) {
        console.log(error);
      });
  };
```
The UI gets a JSON with { key:value} pairs. eg:
``` javascript
{0: 0, 1: 102, 2: 57, 3: 145, 4: 138 }
```
The graph is generated using chart js, every new response dataset is appeneded to the params of the Line component.
## Sentence length: 
`https://us-central1-rishabh-gajra.cloudfunctions.net/sentence_length`
This is a flask function written in python. It uses a regex to parse and calculates a dictionary of number of sentences with legnth as keys.It dumps the data it calculates into a fire store document. The id for this document is parsed from the url. Code snippet for dumping into firestore:
```python
    url = 'http://www.gutenberg.org/files/1342/1342-0.txt'
    length_frequency = {0: 0, 1: 102, 2: 57, 3: 145, 4: 138 }
    db = firestore.Client()
    book_id = url.split('/')[-2]
    doc_ref = db.collection(u'books').document(book_id)
    doc_ref.set({
        u'frequency': json.dumps(length_frequency)
    })
```
where length_frequency is the output dictionary. Fire store instance here is a library provided by google for python flask functions. I have put default values here to show the data structures for variables, they are not hard coded in the actual function.
The regex parser helper function, this is not my work:
```python

    def split_into_sentences(text):
        text = " " + text + "  "
        text = text.replace("\n", " ")
        text = re.sub(prefixes, "\\1<prd>", text)
        text = re.sub(websites, "<prd>\\1", text)
        if "Ph.D" in text:
            text = text.replace("Ph.D.", "Ph<prd>D<prd>")
        text = re.sub("\s" + alphabets + "[.] ", " \\1<prd> ", text)
        text = re.sub(acronyms+" "+starters, "\\1<stop> \\2", text)
        text = re.sub(alphabets + "[.]" + alphabets + "[.]" +
                      alphabets + "[.]", "\\1<prd>\\2<prd>\\3<prd>", text)
        text = re.sub(alphabets + "[.]" + alphabets +
                      "[.]", "\\1<prd>\\2<prd>", text)
        text = re.sub(" "+suffixes+"[.] "+starters, " \\1<stop> \\2", text)
        text = re.sub(" "+suffixes+"[.]", " \\1<prd>", text)
        text = re.sub(" " + alphabets + "[.]", " \\1<prd>", text)
        if "”" in text:
            text = text.replace(".”", "”.")
        if "\"" in text:
            text = text.replace(".\"", "\".")
        if "!" in text:
            text = text.replace("!\"", "\"!")
        if "?" in text:
            text = text.replace("?\"", "\"?")
        text = text.replace(".", ".<stop>")
        text = text.replace("?", "?<stop>")
        text = text.replace("!", "!<stop>")
        text = text.replace("<prd>", ".")
        sentences = text.split("<stop>")
        sentences = sentences[:-1]
        sentences = [s.strip() for s in sentences]
        return sentences
```
source: https://stackoverflow.com/a/31505798/12224110
logs:
![image](https://user-images.githubusercontent.com/25266353/100962169-d3328c00-34f1-11eb-9aeb-2c19c922d4fd.png)

## Cached retriever:
`https://us-central1-rishabh-gajra.cloudfunctions.net/sentence_length`
This function accesses the firestore to check for cached data and return it. The code snippet:
```python
    url = 'http://www.gutenberg.org/files/1342/1342-0.txt'
    book_id = url.split('/')[-2]
    db = firestore.Client()
    doc_ref = db.collection(u'books').document(book_id)
    doc = doc_ref.get()
    if doc.exists:
        freq = json.loads(doc.to_dict()['frequency'])
        response = jsonify({
            'success': True,
            'frequency': freq,
        })
    else:
        response = jsonify({
            'success': False
        })
```
logs
![image](https://user-images.githubusercontent.com/25266353/100962629-af237a80-34f2-11eb-8608-3ce79ce54376.png)
command to deploy and delete gcloud functions:
```bash
gcloud functions deploy sentence_length --runtime python38 --trigger-http --allow-unauthenticated
gcloud functions delete sentence_length
```
## firestore 
This is a key value store that works on collections of documents where each document has a label as attributed. For the purpose of this assignment I created a collection called books where book id was the document id and frequency was a label that stored a stringified version of the following json
```javascript
{0: 0, 1: 102, 2: 57, 3: 145, 4: 138 }
```
Screenshot for the Collection:
![image](https://user-images.githubusercontent.com/25266353/100961367-41764f00-34f0-11eb-85cc-51a78a47fb14.png)
## nginx and gcp VM
Installed ngnix on an ubuntu VM and hosted a website made by building a react website.
## Performance:
Comparing execution times of both functions, its obvious how much time we save:
![image](https://user-images.githubusercontent.com/25266353/100962169-d3328c00-34f1-11eb-9aeb-2c19c922d4fd.png)
![image](https://user-images.githubusercontent.com/25266353/100962629-af237a80-34f2-11eb-8608-3ce79ce54376.png)
As you can see, the difference when a url is cached vs its not is ~3000 ms vs 75ms

# Cost for running all my experiments
This assignment probably cost below 1$. My total cost with the previous assignment is just 3$
## Bugs and improvements:
The UI has bugs. After submtting a request you must select another url by clearing the current selection with hitting the X. If you click analyze again, the UI just does and empty request and gets error as repsonse. The regex parses misses some sentences and thus the nunmber of sentences with 0,1 and 2 words is lot more than it should be. The Front end being on a VM removes the status of serverless from the project but the backend is still serverless.

