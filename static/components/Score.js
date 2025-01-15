const Score = {
  template: `
    <tr>
      <td>{{ student }}</td>
      <td>{{ quiz }}</td>
      <td>{{ score }}</td>
    </tr>
  `,
  props: {
    student: {
      type: String,
      required: true,
    },
    quiz: {
      type: String,
      required: true,
    },
    score: {
      type: Number,
      required: true,
    },
  },
};

export default Score;
