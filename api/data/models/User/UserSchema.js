const findByName = (server, name) => {
  return new Promise((resolve, reject) => {
    const session = server.session();
    session.run('MATCH (user:User {name: {name}}) RETURN user', { name })
    .then((results) => {
      session.close();
      resolve(results.records[0]._fields[0].properties)
    })
    .catch((err) => {
      reject(err);
    })
  });
}

module.exports = {
  findByName
}
