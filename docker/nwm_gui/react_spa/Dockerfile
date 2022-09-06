ARG NODE_VERSION
ARG REACT_APP_NAME

################################################################################################################
ARG NODE_VERSION
FROM node:${NODE_VERSION} AS create_app
ARG REACT_APP_NAME
ENV REACT_APP_NAME=${REACT_APP_NAME}

RUN npx --yes create-react-app /${REACT_APP_NAME:?No react app name set}

# TODO: might want to create special user for things

################################################################################################################
FROM create_app AS react_base

WORKDIR /${REACT_APP_NAME:?}
ENTRYPOINT ["npm", "start"]

################################################################################################################
FROM react_base AS react_dev
ARG TEMP_SRC_DIR=/host_react_sources

# Copy to a temp location first to make sure we can put node_modules/ in place
COPY javascript/${REACT_APP_NAME:-bogus_value} ${TEMP_SRC_DIR}

# Make sure source code from host is in place, combined with modules from build
RUN mv /${REACT_APP_NAME:?No react app name set} /original_app \
    && mv ${TEMP_SRC_DIR} /${REACT_APP_NAME:?} \
    && mv /original_app/node_modules /${REACT_APP_NAME:?}/node_modules

################################################################################################################
FROM react_base AS react_local_dev

COPY ./docker/nwm_gui/react_spa/local_dev_entrypoint.sh /local_dev_entrypoint.sh

RUN chmod ugo+x /local_dev_entrypoint.sh && apt-get update && apt-get install -y rsync

ENTRYPOINT ["/local_dev_entrypoint.sh"]

################################################################################################################
FROM react_dev
# Create a minified bundle for production
RUN npm run build