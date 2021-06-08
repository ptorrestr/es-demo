# ES demo

## Run

You might need to set `max_map_count=262144` in your system in order to run Elastic Search as containers.

```bash
sysctl -w vm.max_map_count=262144
```

We assume that:

- You have `Python` in virtual environment (We provide files for `pipenv` files, and `requirements.txt` for `pip`)
- `docker` and `docker-compose` are available. Feel free to explore the images we are using in the `docker-compose.yml` file in case you have any security concerns.

Please, install the dependencies using one of the methods listed below:

- `pip install -r requirements.txt`
- `pipenv install`

## Q1

There are multiple alternatives to index the data in a multi-language context using ElasticSearch.

The simplest model is to build a specific index for each language (or language-country combination).
We call this approach: __multi index__.
In this scenario, the language-dependent data is analyzed using a particular strategy for the language-country combination and stored alone in a particular index.

The main benefits of this approach are the speed at query time as the index has fewer fields to examine per query.
Moreover, since there is only one index, there is no need to determine the language of the query and the solution can scale with the number of languages.

However, there are some points to consider:

- As the number of language-country combinations grows, so will the number of indices to maintain, making the addition of new languages more expensive.
- The use of storage capacity is inefficient as space can be saved if different analyzers are conducted under the same fields. This might be relevant for countries with the same language, and minor idioms between them.
- Fields whose content has mixed language are going to be replicated as many times as needed.

Another approach is to build a single index and include as many analyzers as needed for each language of interest.
In this solution (we called __multi mappings__), the fields are going to be indexed using language-aware analyzers that will consider the particularities of each language.
Then, the system will create models for each field without replicating the text.

The main gain of this approach is controlling the storage inefficiencies observed in the previous the __multi-index__ approach. Plus, it makes the support of the index simpler as there is no need to maintain several indices.

Some cons in this approach are:

- The mappings are more complex and maintaining them might get _tricky_.
- The performance of the index might get hurt, especially if the number of language-country combinations is high.

### Example code Q1

We created a simple code to index data using the __multi-index__ approach.

We included a sample dataset (file: `productos_cleaned.csv`).
This dataset is a list of grocery products, including the description of them and categories.

For this example, we assume the field `description` in our dataset is multi-language and we created two meta fields, one for Spanish and another for Portuguese.

You can get the answer for this solution by running:

```bash
pytest tests/test_q1.py -s
```

## Q2

Many components play a major role when determining the relevance score between the items and the query.
Any improvement in this score will need to consider these components:

1. __The scoring (or similarity) function__: The function that determines the similarity between the query and the documents (e.g. products, shops, etc). In this regard, `BM25` is one of the most widely used heuristics and have been extensively evaluated in many use-cases. Still, there are plenty of options in the literature that can be considered for this role [1].
2. __The structure of the documents__: Historically, inverted indexes are based on flat text document retrieval. However, this can be adapted to more sophisticated scenarios where the items of interest are structured. For example, if the schema of the items is composed of three fields: _category_, _tags_, and _description_, then we can leverage the relevance of these fields using different heuristics such as weighted average, softmax, etc.
3. __Vector space and embeddings__: Typically, items are represented in the language using a _vector space_, in which each component represents a particular word or term. Since the terms of the queries are user-dependent, there are high chances new terms might appear in the query. This gap between the language of the queries and the items can be controlled using stemming (reduce a term to its root based on prefixes and suffixes) or lemmatization (similar to stemming but based on language-dependent ontologies). The same objective can be achieved by using supervised models to create word embedding models, in which the components of their vector spaces represent the semantics of the language rather than pure lexical terms.

The evaluation of the relevance score has been extensively discussed in the literature [1]. Some examples are:

- __Precision & recall @ K__: Here the retrieval process is seen as a binary classification problem, in which the system under evaluation _must determine which item is relevant at the top k positions_. The dataset consists of queries whose results have been annotated as relevant and not relevant. The problem can then be evaluated as any other classification model.
- __Mean Average Precision (mAP) @ K__: Since the user wants to have its response at the top of the result list, it is necessary to incorporate such expectation in the evaluation process. _mAP@k_ aims to resolve this by repeatedly evaluating the average precision at the top-_k_ list and then obtaining the mean among them. The average precision evaluates how well the retrieval process is obtaining relevant items at each position of the top-$k$ list. Relevant items at the top positions will have a major impact on the score than items at the end of the result list.
- __Normalized Discounted Cumulative Gain (nDCG) @ K__: Although _mAP_ considers the position of the relevant items in the result, it cannot consider the weight of relevant items, _i.e._ some items are more relevant than others. This can be solved using the well-known heuristic DCG. This evaluation compares the resulting and expected rankings and measures the divergence between them based on a logarithmic function. Since this metric measures the divergence, the relevance of the item is not limited to a binary model. Thus, we can employ graded relevance models.
- __Correlations & Kendall-$\tau$__: Since the output of the retrieval process is a ranking, we can simply measure the correlation between them and the expected ranking.

The default relevance in Lucene (and by extension ElasticSearch) is BM25. BM25 is a well-established heuristic that combines several well-known principles into a single equation: term frequency, document length and inverse document frequency [2].
Despite BM25 not being derived from any theoretical framework, it has been applied to a wide range of problems successfully.
Still, improving BM25 is possible and is largely subjected to the domain of the documents.
For example, if we consider the items to be more like _entities_ (in the sense that they are composed of fields), there are several techniques that can be used to improve the search, especially considering that entities might have relations among themselves [3].
Therefore, without any knowledge of the data and the queries, it is difficult to propose a new relevance function.

## Q3

Many variables are available to personalize the results.
For instance, the user's geographic location, previous searches, user's interest or profile.
We can implement the personalization in ElasticSearch using segmentation, i.e. define cohorts of users according to the queries performed in the past, or any other user model that can identify the preferences of the users.

### Example code Q3

Let's say we have a user interested in __wines__.
We can include in the query terms related to such interest and filter the result accordingly.
Since our example dataset has a field for categories (`group`), we can filter in that particular field following the user's interest, as shown below:

```json
{
    "query": {
        "bool": {
            "must": [
                {
                    "match": {
                        "description.spanish": "blanco"
                    }
                }
            ],
            "filter": [
                {
                    "term": {
                        "group": "vinos"
                    }
                }
            ]
        }
    }
}
```

Notice that we can include as many filters as we want.
More complex queries can also be considered, like multi-field matching or manipulation of the thresholds.

You can test our example with the following command:

```bash
pytest tests/test_q3.py -s
```

The output of the query `'queries/q3_c1_es.json` shows the results biased towards the category `wine` while the results in  `'queries/q3_c2_es.json` are intermingling different categories.

## Q4

ElasticSearch allows us to update items in the index.
However, this feature must be used with caution as it might take time to update a large collection of documents.
Fortunately, ElasticSearch provides a bulk API to handle expensive insertions and updates.

In this way, we can implement a data pipeline that takes the new data/updates and generates a call of the bulk API
The insertions and updates can be divided into several requests, and handle over to the ES in an orderly maner.
The pipeline must be scheduled in off-pick hours to reduce the pressure of large changes in the indices.

## Q5

High CPU usage might be related to:

1. __JVM issues__: the JVM does not have enough space and the garbage collector is monopolizing the CPU. Incrementing the heap size might solve this problem.
2. __Load imbalance__: This is likely when a subset of nodes have higher CPU usage than others.
3. __Memory swapping__: If the machine does not have enough RAM, then the system is likely to enter into _thrashing_.
4. __Indexing issues__: If the CPU usage is high when indexing, then it implies that the strategy in the construction of the index might be wrong. Consider that the insertion and update of items need to be handled in off-pick hours.
5. __Query issues__: Some queries might be too expensive. Consider the use of filters or reduce the size of the response. Also, think about the use of cache memories for repetitive and expensive queries.
6. __Too many indices__: A large number of replicas and shards might degrade the performance when the machine is not big enough.

## Q6

High disk usage might be related to:

1. __Indexing issues__: Fields that are not searchable should be removed from the mappings.
2. __Shards__: Smaller shards are inefficient in terms of storage. Consider larger ones.
3. __Zombie indices__: Indices that are not used (or they are old) should be removed. These can be later recreated from snapshots if needed.
4. __High replicas__: Reduce the number of replicas (especially for old indices)

## Q7

Let's assume we have the following data:

```csv
ID | TIMESTAMP | TERMS
```

where `ID` is the id of the request, `TIMESTAMP` is the time of the request and `TERMS` is the term of the request.

We can then create a visalization in Kibana such that similar terms are grouped if they are identical.

You can generate the dashboard using the following commands:

```bash
docker-compose up -d
pytest --docker-compose-no-build --use-running-containers tests/test_q7.py -s
```

Now visit [http://localhost:5601/app/dashboards#/view/ba239930-c80c-11eb-9d02-f17a79c9ce20](http://localhost:5601/app/dashboards#/view/ba239930-c80c-11eb-9d02-f17a79c9ce20)

Once you finish, you can stop docker:

```bash
docker-compose down
```

## References

- [1] Baeza-Yates, Ricardo, and Berthier Ribeiro-Neto. Modern information retrieval. Vol. 463. New York: ACM press, 1999.
- [2] Lavrenko, Victor. A generative theory of relevance. Vol. 26. Springer Science & Business Media, 2008.
- [3] Torres-Tramón, Pablo, Mohan Timilsina, and Conor Hayes. "A diffusion-based method for entity search." 2019 IEEE 13th International Conference on Semantic Computing (ICSC). IEEE, 2019.
