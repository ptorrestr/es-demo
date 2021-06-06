# ES demo

## Run

You need to set `max_map_count=262144`

```bash
sysctl -w vm.max_map_count=262144
```


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

### Solution Q1

We created a simple code to index data using the __multi-index__ approach.
We assume the field `description` in our dataset is multi-language and created two fields for Spanish and Portuguese.

You can get the answer for this solution by running:

```bash
pytest tests/test_q1.py
```

## Q2
