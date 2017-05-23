const findByName = (server, name) =>
  new Promise((resolve, reject) => {
    const session = server.session();
    session.run('MATCH (user:User {name: {name}}) RETURN user.id as id, user.name as name', { name })
    .then(({ records }) => {
      session.close();
      const user = records.map(record => ({
        id: record.get('id').toNumber(),
        name: record.get('name')
      }));
      resolve(user[0]);
    })
    .catch((err) => {
      reject(err);
    });
  }
);

module.exports = {
  findByName
};
