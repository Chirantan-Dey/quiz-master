const Chapter = {
  template: `
    <tr>
      <td>{{ name }}</td>
      <td>{{ description }}</td>
    </tr>
  `,
  props: {
    name: {
      type: String,
      required: true,
    },
    description: {
      type: String,
      required: true,
    },
  },
};

export default Chapter;
