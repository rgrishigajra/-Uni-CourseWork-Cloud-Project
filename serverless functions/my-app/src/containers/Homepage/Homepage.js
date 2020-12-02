import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import { TextField, Button } from '@material-ui/core';
import axios from 'axios';
import './Homepage.css';
import { Puff } from '@agney/react-loading';
import Autocomplete from '@material-ui/lab/Autocomplete';

const options = {
  scales: {
    yAxes: [
      {
        ticks: {
          beginAtZero: true,
        },
      },
    ],
  },
  title: {
    display: true,
    text: 'Ditribution of number of words in each sentence.',
  },
};
const textUrls = [
  {
    title: 'Frankenstein by Mary Wollstonecraft Shelley',
    url: 'http://www.gutenberg.org/files/84/84-0.txt',
  },
  {
    title: 'Pride and Prejudice by Jane Austen',
    url: 'http://www.gutenberg.org/files/1342/1342-0.txt',
  },
  {
    title: "Alice's Adventures in Wonderland by Lewis Carroll",
    url: 'http://www.gutenberg.org/files/11/11-0.txt',
  },
  {
    title: 'Moby Dick by Herman Melville',
    url: 'http://www.gutenberg.org/files/2701/2701-0.txt',
  },
  {
    title: 'Dracula by Bram Stoker',
    url: 'http://www.gutenberg.org/cache/epub/345/pg345.txt',
  },
  {
    title: 'Peter Pan by James M. Barrie',
    url: 'http://www.gutenberg.org/files/16/16-0.txt',
  },
  {
    title: 'The Republic by Plato',
    url: 'http://www.gutenberg.org/cache/epub/1497/pg1497.txt',
  },
];
function Homepage() {
  const [datasets, setData] = useState([]);
  const [label, setLabel] = useState('');
  const [url, setURL] = useState('');
  const [loading, setLoading] = useState(false);
  const sendRequest = () => {
    setLoading(true);
    const u = url;
    setURL('');
    const l = label;
    setLabel('');
    axios
      .post(
        `https://us-central1-rishabh-gajra.cloudfunctions.net/sentence_length`,
        {
          url: u,
        }
      )
      .then((res) => {
        console.log(res.data.frequency);
        updateDataSet(l, Object.values(res.data.frequency));
        setLoading(false);
      })
      .catch(function (error) {
        console.log(error);
      });
  };
  const autoFunction = (textUrl) => {
    setLabel(textUrl.title);
    setURL(textUrl.url);
    return textUrl.url;
  };
  const updateDataSet = (name, data) => {
    const red = Math.random() * 255;
    const blue = Math.random() * 255;
    const green = Math.random() * 255;
    const newSet = {
      label: name,
      data: data,
      fill: false,
      backgroundColor: `rgb(${red}, ${blue}, ${green})`,
      borderColor: `rgba(${red}, ${blue}, ${green}, 0.2)`,
    };
    const oldDatasets = datasets;
    setData([...oldDatasets, newSet]);
  };

  return (
    <div className="body-container">
      <div>
        {loading && (
          <div className="loading">
            <Puff width="100" />
          </div>
        )}
        <div className="title">
          The App parses the plain text from the urls and draws a histogram of
          the sentence length distribution.
        </div>
        <div>Enter a book name and url with text</div>
        <br />
        <div className="header">
          <TextField
            placeholder="Book name here"
            id="outlined-basic"
            label="Book name"
            variant="outlined"
            value={label}
            style={{ width: 500 }}
            required={true}
            onChange={(event) => {
              setLabel(event.target.value);
            }}
          />
          <Autocomplete
            selectOnFocus
            clearOnBlur
            handleHomeEndKeys
            options={textUrls}
            style={{ width: 500 }}
            renderOption={(textUrls) => textUrls.title}
            getOptionLabel={autoFunction}
            freeSolo
            renderInput={(params) => (
              <TextField
                {...params}
                placeholder="http://www.gutenberg.org/files/1342/1342-0.txt"
                id="outlined-basic"
                label="Url"
                required={true}
                variant="outlined"
                style={{ width: 500 }}
                value={url}
                onChange={(event) => {
                  setURL(event.target.value);
                }}
              />
            )}
          />

          <Button
            color="secondary"
            onClick={() => {
              sendRequest();
            }}
          >
            Analyse
          </Button>
          <Button
            color="secondary"
            onClick={() => {
              setURL('');
              setLabel('');
              setData([]);
            }}
          >
            Reset
          </Button>
        </div>
      </div>
      <div className='chart'>
      <Line
        data={{
          labels: [...Array(60).keys()],
          datasets: datasets,
        }}
        options={options}
      />
      </div>
    </div>
  );
}

export default Homepage;
