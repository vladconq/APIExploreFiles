# APIExploreFiles
## Test Project for EPAM

[SERVER ADDRESS](https://api-explore-files.herokuapp.com/).

- To display the contents of the server folder, just type the server address.  

- To display information about a specific file, type its index in the following format: 

> https://api-explore-files.herokuapp.com/file=2 (index must be positive integer)

- To display information about a specific word, type it in the following format: 

> https://api-explore-files.herokuapp.com/word=python (word must be in English or Russian)

- The API works with the main file extensions, such as '*txt, docx, html.*'
To display files of a specific format, type the desired extension in the following format:

> https://api-explore-files.herokuapp.com/ext=txt

The application consists of three classes:

**class WordInfo()** - The class is designed to handle words. This class implements functions that calculate the number of syllables, the number of vowels and consonants. Correctly processed words of English and Russian.

**class FileInfo()** - The class is designed to handle files. This class implements functions that define file extensions, encoding, text splitting into words, the most frequent and rare words, the average word length, the ratio of syllables to words, and the total number of vowels and consonants in the file.

**class FolderInfo()** - The class is designed to handle folders. This class implements functions that display a list of folders and files in the server folder. The class is able to filter files by the extension specified by the user.
