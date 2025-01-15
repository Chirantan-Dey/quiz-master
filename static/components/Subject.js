const Subject = {
  template: `
    <tr>
      <td>{{ name }}</td>
      <td>{{ creator }}</td>
    </tr>
  `,
  props: {
    name: {
      type: String,
      required: true,
    },
    creator: {
      type: String,
      required: true,
    },
  },
};

export default Subject;
